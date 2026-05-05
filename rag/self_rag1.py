"""Self-RAG nâng cao: Batch relevance filtering + Multi-score confidence + Citations.

Kiến trúc giống doc 8 nhưng dùng Ollama (local) thay vì Gemini.
Tự khởi tạo LLM bên trong __init__ — tích hợp trực tiếp vào project.

Pipeline mỗi hop:
  1. Query Rewriting       : LLM viết lại + sinh sub-queries
  2. Retrieve              : Lấy docs từ retriever
  3. Batch Relevance Filter: LLM chấm điểm từng chunk, lọc theo threshold
  4. Generate              : Sinh câu trả lời từ chunks đã lọc
  5. Combined Eval         : Đánh giá support (ISSUP) + utility (ISUSE)
  6. Follow-up             : Nếu cần → thêm follow_up_query vào queue hop tiếp
  7. Synthesize            : Tổng hợp kết quả nếu multi-hop
  8. Confidence            : Tính từ 3 thành phần relevance + support + utility

Cấu hình qua config.py:
  OLLAMA_MODEL, OLLAMA_BASE_URL
  SELF_RAG_MAX_HOPS, SELF_RAG_CONFIDENCE_THRESHOLD
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_ollama import ChatOllama

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_REPEAT_PENALTY,
    LLM_NUM_PREDICT,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class QueryRewriteResult:
    """Kết quả bước query rewriting."""
    original: str
    rewritten: str
    sub_queries: list[str] = field(default_factory=list)
    latency_ms: float = 0.0


@dataclass
class RetrievedChunk:
    """Một chunk được retrieve kèm điểm relevance."""
    document: Any
    relevance_score: float = 0.0
    is_relevant: bool = True
    relevance_reason: str = ""


@dataclass
class GenerationResult:
    """Kết quả sinh câu trả lời và đánh giá chất lượng."""
    answer: str
    context_used: list[str] = field(default_factory=list)
    is_supported: bool = True
    support_score: float = 0.7
    is_useful: bool = True
    utility_score: float = 0.7
    latency_ms: float = 0.0


@dataclass
class HopResult:
    """Kết quả một hop trong multi-hop reasoning."""
    hop_index: int
    query: str
    retrieved_chunks: list[RetrievedChunk]
    generation: GenerationResult
    follow_up_needed: bool = False
    follow_up_query: str = ""


@dataclass
class SelfRagAdvancedResult:
    """Kết quả toàn bộ quá trình Self-RAG nâng cao."""
    final_answer: str
    confidence: float
    query_rewrite: QueryRewriteResult
    hops: list[HopResult]
    citations: list[dict]
    total_latency_ms: float = 0.0
    relevance_score: float = 0.0
    support_score: float = 0.0
    utility_score: float = 0.0
    retrieval_count: int = 0
    filtered_count: int = 0

    def to_dict(self) -> dict:
        return {
            "confidence": round(self.confidence, 3),
            "relevance_score": round(self.relevance_score, 3),
            "support_score": round(self.support_score, 3),
            "utility_score": round(self.utility_score, 3),
            "hops": len(self.hops),
            "retrieval_count": self.retrieval_count,
            "filtered_count": self.filtered_count,
            "final_query": self.query_rewrite.rewritten,
            "total_latency_ms": round(self.total_latency_ms, 1),
            "citations": self.citations[:5],
            "hop_details": [
                {
                    "hop": h.hop_index,
                    "query": h.query,
                    "chunks_retrieved": len(h.retrieved_chunks),
                    "chunks_relevant": sum(1 for c in h.retrieved_chunks if c.is_relevant),
                    "support_score": round(h.generation.support_score, 3),
                    "utility_score": round(h.generation.utility_score, 3),
                    "follow_up_needed": h.follow_up_needed,
                }
                for h in self.hops
            ],
        }


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_REWRITE_PROMPT_VI = """Viết lại câu hỏi tìm kiếm rõ hơn và tạo tối đa 2 sub-queries bổ sung.

Câu hỏi: {question}

Trả về JSON (chỉ JSON, không giải thích):
{{
  "rewritten": "câu hỏi viết lại rõ ràng hơn",
  "sub_queries": ["sub-query 1", "sub-query 2"]
}}"""

_REWRITE_PROMPT_EN = """Rewrite the search query to be clearer and create up to 2 additional sub-queries.

Question: {question}

Return JSON (JSON only, no explanation):
{{
  "rewritten": "rewritten clearer question",
  "sub_queries": ["sub-query 1", "sub-query 2"]
}}"""

_BATCH_RELEVANCE_PROMPT_VI = """Đánh giá độ liên quan của các đoạn văn bản sau với câu hỏi.

Câu hỏi: {question}

Các đoạn văn (đánh số từ 0):
{passages}

Trả về JSON (chỉ JSON) — mảng điểm tương ứng với từng đoạn:
{{
  "scores": [0.8, 0.3, 0.9, ...]
}}

Lưu ý: scores[i] là điểm liên quan của đoạn thứ i, từ 0.0 đến 1.0."""

_BATCH_RELEVANCE_PROMPT_EN = """Evaluate the relevance of the following passages to the question.

Question: {question}

Passages (numbered from 0):
{passages}

Return JSON (JSON only) — array of scores for each passage:
{{
  "scores": [0.8, 0.3, 0.9, ...]
}}

Note: scores[i] is the relevance score of passage i, from 0.0 to 1.0."""

_GENERATION_PROMPT_VI = """Bạn là trợ lý AI phân tích tài liệu. Trả lời câu hỏi DỰA HOÀN TOÀN vào ngữ cảnh.

NGUYÊN TẮC:
- Chỉ dùng thông tin trong ngữ cảnh dưới đây
- Nếu không đủ thông tin, nói rõ phần nào còn thiếu
- Văn bản thuần, không dùng markdown

NGỮ CẢNH:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""

_GENERATION_PROMPT_EN = """You are an AI assistant analyzing documents. Answer the question BASED ENTIRELY on the context.

PRINCIPLES:
- Only use information from the context below
- If information is insufficient, clearly state what is missing
- Plain text, no markdown

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

_COMBINED_EVAL_PROMPT_VI = """Đánh giá câu trả lời theo 2 tiêu chí.

Câu hỏi: {question}

Ngữ cảnh dùng để trả lời:
{context}

Câu trả lời:
{answer}

Tiêu chí 1 — Grounded (ISSUP): câu trả lời có bám sát ngữ cảnh không?
Tiêu chí 2 — Useful (ISUSE): câu trả lời có đầy đủ, hữu ích không?

Trả về JSON (chỉ JSON):
{{
  "support_score": 0.0-1.0,
  "utility_score": 0.0-1.0,
  "follow_up_needed": true/false,
  "follow_up_query": "câu hỏi bổ sung nếu cần, hoặc empty string"
}}"""

_COMBINED_EVAL_PROMPT_EN = """Evaluate the answer according to 2 criteria.

Question: {question}

Context used to answer:
{context}

Answer:
{answer}

Criterion 1 — Grounded (ISSUP): Is the answer grounded in the context?
Criterion 2 — Useful (ISUSE): Is the answer complete and useful?

Return JSON (JSON only):
{{
  "support_score": 0.0-1.0,
  "utility_score": 0.0-1.0,
  "follow_up_needed": true/false,
  "follow_up_query": "follow-up question if needed, or empty string"
}}"""


# ---------------------------------------------------------------------------
# SelfRagAdvanced
# ---------------------------------------------------------------------------

class SelfRagAdvanced:
    """
    Self-RAG nâng cao dùng Ollama local.

    Tự khởi tạo LLM bên trong — tích hợp trực tiếp vào Chain:
        self.self_rag_advanced = SelfRagAdvanced(retriever=self.retriever)
        result = self.self_rag_advanced.run(question, language)

    Khác biệt so với SelfRag (v2):
      - Batch relevance filtering: LLM chấm điểm từng chunk trước khi generate
      - Confidence đa chiều: relevance × 0.30 + support × 0.40 + utility × 0.30
      - Citations tự động từ chunks được dùng
      - Follow-up query: LLM đề xuất câu hỏi bổ sung thay vì chỉ rewrite
      - Queue-based multi-hop: queries_to_run append follow_up_query
      - Bilingual prompts: tự chọn VI/EN theo language parameter
    """

    # Ngưỡng từ để coi là câu hỏi ngắn
    _SHORT_QUERY_WORD_LIMIT = 4
    # Threshold thấp hơn cho câu hỏi ngắn
    _SHORT_QUERY_THRESHOLD = 0.25
    # Số chunks tối thiểu cho generation khi relevant_chunks ít
    _MIN_CHUNKS_FOR_GEN = 5

    def __init__(
        self,
        retriever,
        max_hops: int = 2,
        relevance_threshold: float = 0.45,
        support_threshold: float = 0.6,
        top_k_per_query: int = 5,
    ):
        self.retriever = retriever
        self.max_hops = max_hops
        self.relevance_threshold = relevance_threshold
        self.support_threshold = support_threshold
        self.top_k_per_query = top_k_per_query

        # Tự khởi tạo LLM Ollama bên trong
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=LLM_TEMPERATURE,
            top_p=LLM_TOP_P,
            repeat_penalty=LLM_REPEAT_PENALTY,
            num_predict=LLM_NUM_PREDICT,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, question: str, language: str = "vi") -> SelfRagAdvancedResult:
        """
        Chạy Self-RAG nâng cao.

        Args:
            question: Câu hỏi gốc của người dùng
            language: "vi" hoặc "en" — chọn prompt phù hợp

        Returns:
            SelfRagAdvancedResult với answer, confidence, citations, hop details
        """
        t_start = time.perf_counter()

        # Bước 1: Rewrite query
        rewrite_result = self._rewrite_query(question, language)

        hops: list[HopResult] = []
        all_citations: list[dict] = []

        # Queue-based multi-hop: bắt đầu với rewritten query
        queries_to_run = [rewrite_result.rewritten]

        for hop_idx in range(self.max_hops):
            if hop_idx >= len(queries_to_run):
                break

            query = queries_to_run[hop_idx]
            hop = self._run_hop(question, query, hop_idx, language, all_citations)
            hops.append(hop)

            # Nếu LLM đề xuất follow-up và còn hop → thêm vào queue
            if (
                hop.follow_up_needed
                and hop.follow_up_query
                and hop_idx + 1 < self.max_hops
            ):
                queries_to_run.append(hop.follow_up_query)
                logger.info(
                    "Self-RAG hop=%d: follow-up query=%r", hop_idx, hop.follow_up_query
                )

        # Tổng hợp kết quả nếu multi-hop
        final_answer = self._synthesize(question, hops, language)
        confidence, scores = self._compute_confidence(hops)
        total_ms = (time.perf_counter() - t_start) * 1000

        logger.info(
            "Self-RAG Advanced done | hops=%d | confidence=%.3f | latency=%.0fms",
            len(hops), confidence, total_ms,
        )

        return SelfRagAdvancedResult(
            final_answer=final_answer,
            confidence=confidence,
            query_rewrite=rewrite_result,
            hops=hops,
            citations=all_citations[:8],
            total_latency_ms=total_ms,
            relevance_score=scores["relevance"],
            support_score=scores["support"],
            utility_score=scores["utility"],
            retrieval_count=sum(len(h.retrieved_chunks) for h in hops),
            filtered_count=sum(
                sum(1 for c in h.retrieved_chunks if c.is_relevant) for h in hops
            ),
        )

    # ------------------------------------------------------------------
    # Step 1: Query Rewriting
    # ------------------------------------------------------------------

    def _rewrite_query(self, question: str, language: str) -> QueryRewriteResult:
        t0 = time.perf_counter()
        try:
            template = _REWRITE_PROMPT_VI if language == "vi" else _REWRITE_PROMPT_EN
            raw = self._call_llm(template.format(question=question))
            data = self._parse_json(raw)

            sub_queries = data.get("sub_queries", [])
            if not isinstance(sub_queries, list):
                sub_queries = []
            sub_queries = [str(q).strip() for q in sub_queries if q][:2]

            return QueryRewriteResult(
                original=question,
                rewritten=str(data.get("rewritten") or question).strip(),
                sub_queries=sub_queries,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            logger.warning("Query rewrite thất bại (%s), dùng câu hỏi gốc", exc)
            return QueryRewriteResult(
                original=question,
                rewritten=question,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

    # ------------------------------------------------------------------
    # Single hop
    # ------------------------------------------------------------------

    def _run_hop(
        self,
        original_question: str,
        query: str,
        hop_idx: int,
        language: str,
        citations_acc: list[dict],
    ) -> HopResult:
        # Retrieve
        raw_docs = self._retrieve(query)

        # Batch relevance filter với adaptive threshold
        effective_threshold = self._adaptive_threshold(query)
        filtered = self._batch_filter_relevance(query, raw_docs, effective_threshold, language)

        relevant_chunks = [c for c in filtered if c.is_relevant]

        # Fallback: lấy nhiều chunks hơn nếu relevant_chunks quá ít
        min_needed = min(self._MIN_CHUNKS_FOR_GEN, len(filtered))
        chunks_for_gen = (
            relevant_chunks
            if len(relevant_chunks) >= min_needed
            else filtered[:min_needed]
        )

        # Generate
        context = self._build_context(chunks_for_gen)
        gen = self._generate(original_question, context, language)

        # Combined eval (ISSUP + ISUSE + follow-up)
        follow_up_needed, follow_up_query = False, ""
        if gen.answer and context.strip():
            gen, follow_up_needed, follow_up_query = self._combined_eval(
                gen, original_question, context, language
            )

        # Thu thập citations từ top chunks
        for chunk in chunks_for_gen[:3]:
            meta = dict(getattr(chunk.document, "metadata", {}) or {})
            citations_acc.append({
                "source_name": (
                    meta.get("source_name") or meta.get("source") or "Không rõ nguồn"
                ),
                "page_number": meta.get("page_number"),
                "chunk_id": meta.get("chunk_id"),
                "context": getattr(chunk.document, "page_content", "")[:200],
                "relevance_score": round(chunk.relevance_score, 3),
                "hop": hop_idx,
            })

        logger.info(
            "Self-RAG hop=%d | query=%r | retrieved=%d | relevant=%d | "
            "support=%.2f | utility=%.2f",
            hop_idx, query, len(raw_docs), len(relevant_chunks),
            gen.support_score, gen.utility_score,
        )

        return HopResult(
            hop_index=hop_idx,
            query=query,
            retrieved_chunks=filtered,
            generation=gen,
            follow_up_needed=follow_up_needed,
            follow_up_query=follow_up_query,
        )

    # ------------------------------------------------------------------
    # Adaptive threshold
    # ------------------------------------------------------------------

    def _adaptive_threshold(self, query: str) -> float:
        """Câu hỏi ngắn ≤ 4 từ → threshold thấp hơn để tránh lọc mất thông tin."""
        word_count = len(query.strip().split())
        if word_count <= self._SHORT_QUERY_WORD_LIMIT:
            logger.debug(
                "Câu hỏi ngắn (%d từ): threshold=%.2f thay vì %.2f",
                word_count, self._SHORT_QUERY_THRESHOLD, self.relevance_threshold,
            )
            return self._SHORT_QUERY_THRESHOLD
        return self.relevance_threshold

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def _retrieve(self, query: str) -> list[RetrievedChunk]:
        """Lấy docs từ retriever an toàn, trả về [] nếu retriever None."""
        if self.retriever is None:
            logger.warning("Retriever chưa được khởi tạo, trả về danh sách rỗng")
            return []
        try:
            if hasattr(self.retriever, "invoke"):
                docs = self.retriever.invoke(query) or []
            else:
                docs = self.retriever.get_relevant_documents(query) or []
        except Exception as exc:
            logger.warning("Retrieval thất bại: %s", exc)
            docs = []
        return [RetrievedChunk(document=doc, relevance_score=0.0) for doc in docs]

    # ------------------------------------------------------------------
    # Batch relevance filter
    # ------------------------------------------------------------------

    def _batch_filter_relevance(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        threshold: Optional[float] = None,
        language: str = "vi",
    ) -> list[RetrievedChunk]:
        """LLM chấm điểm từng chunk cùng lúc, lọc theo threshold."""
        if not chunks:
            return chunks

        effective = threshold if threshold is not None else self.relevance_threshold

        passages_text = "\n\n".join(
            f"[{i}] {getattr(c.document, 'page_content', '')[:400]}"
            for i, c in enumerate(chunks)
        )

        template = (
            _BATCH_RELEVANCE_PROMPT_VI if language == "vi"
            else _BATCH_RELEVANCE_PROMPT_EN
        )

        try:
            raw = self._call_llm(
                template.format(question=query, passages=passages_text)
            )
            data = self._parse_json(raw)
            scores = data.get("scores", [])

            # Bảo vệ khi scores không phải list
            if not isinstance(scores, list):
                logger.warning("scores không phải list: %r, giữ tất cả chunks", scores)
                scores = []

            for i, chunk in enumerate(chunks):
                raw_score = scores[i] if i < len(scores) else 0.5
                try:
                    score = float(raw_score)
                except (TypeError, ValueError):
                    logger.warning("scores[%d] không hợp lệ: %r, dùng 0.5", i, raw_score)
                    score = 0.5
                chunk.relevance_score = max(0.0, min(1.0, score))
                chunk.is_relevant = chunk.relevance_score >= effective

        except Exception as exc:
            logger.warning("Batch relevance filter thất bại (%s), giữ tất cả chunks", exc)
            for chunk in chunks:
                chunk.relevance_score = 0.6
                chunk.is_relevant = True

        return chunks

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def _generate(self, question: str, context: str, language: str) -> GenerationResult:
        t0 = time.perf_counter()

        if not context.strip():
            no_info = (
                "Không tìm thấy thông tin liên quan trong tài liệu."
                if language == "vi"
                else "No relevant information found in the document."
            )
            return GenerationResult(
                answer=no_info,
                is_supported=False,
                support_score=0.0,
                is_useful=False,
                utility_score=0.0,
            )

        template = _GENERATION_PROMPT_VI if language == "vi" else _GENERATION_PROMPT_EN
        try:
            answer = self._call_llm(template.format(context=context, question=question))
            if not answer or not answer.strip():
                answer = (
                    "Không thể sinh câu trả lời từ ngữ cảnh hiện tại."
                    if language == "vi"
                    else "Unable to generate an answer from the current context."
                )
        except Exception as exc:
            logger.error("Generation LLM call thất bại: %s", exc, exc_info=True)
            raise RuntimeError(f"Lỗi khi gọi Ollama: {exc}") from exc

        return GenerationResult(
            answer=answer,
            context_used=[context[:300]],
            latency_ms=(time.perf_counter() - t0) * 1000,
        )

    # ------------------------------------------------------------------
    # Combined eval (ISSUP + ISUSE + follow-up)
    # ------------------------------------------------------------------

    def _combined_eval(
        self,
        gen: GenerationResult,
        question: str,
        context: str,
        language: str,
    ) -> tuple[GenerationResult, bool, str]:
        template = (
            _COMBINED_EVAL_PROMPT_VI if language == "vi"
            else _COMBINED_EVAL_PROMPT_EN
        )
        try:
            raw = self._call_llm(
                template.format(
                    question=question,
                    context=context[:1000],
                    answer=gen.answer[:600],
                )
            )
            data = self._parse_json(raw)

            raw_support = data.get("support_score", 0.7)
            raw_utility = data.get("utility_score", 0.7)
            try:
                gen.support_score = max(0.0, min(1.0, float(raw_support)))
            except (TypeError, ValueError):
                gen.support_score = 0.7
            try:
                gen.utility_score = max(0.0, min(1.0, float(raw_utility)))
            except (TypeError, ValueError):
                gen.utility_score = 0.7

            gen.is_supported = gen.support_score >= self.support_threshold
            gen.is_useful = gen.utility_score >= 0.5
            follow_up_needed = bool(data.get("follow_up_needed", False))
            follow_up_query = str(data.get("follow_up_query", "")).strip()

        except Exception as exc:
            logger.warning("Combined eval thất bại (%s), dùng default scores", exc)
            gen.support_score = 0.7
            gen.utility_score = 0.7
            follow_up_needed = False
            follow_up_query = ""

        return gen, follow_up_needed, follow_up_query

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    def _synthesize(
        self, original_question: str, hops: list[HopResult], language: str
    ) -> str:
        """Tổng hợp kết quả từ nhiều hops thành câu trả lời cuối."""
        if not hops:
            return (
                "Không có đủ thông tin để trả lời câu hỏi này."
                if language == "vi"
                else "Not enough information to answer this question."
            )

        # Single hop: trả về thẳng
        if len(hops) == 1:
            return hops[0].generation.answer

        # Multi-hop: tổng hợp
        hops_summary = "\n\n".join(
            f"[Bước {h.hop_index + 1}]\n{h.generation.answer}"
            for h in hops
        )
        synthesize_prompt = (
            f"Tổng hợp các thông tin sau thành câu trả lời mạch lạc.\n\n"
            f"{hops_summary}\n\n"
            f"CÂU HỎI: {original_question}\n\n"
            f"TRẢ LỜI TỔNG HỢP (văn bản thuần, không markdown):"
            if language == "vi"
            else
            f"Synthesize the following information into a coherent answer.\n\n"
            f"{hops_summary}\n\n"
            f"QUESTION: {original_question}\n\n"
            f"SYNTHESIZED ANSWER (plain text, no markdown):"
        )
        try:
            return self._call_llm(synthesize_prompt)
        except Exception as exc:
            logger.warning("Synthesis thất bại: %s", exc)
            # Fallback: lấy hop có utility_score cao nhất
            return max(hops, key=lambda h: h.generation.utility_score).generation.answer

    # ------------------------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------------------------

    def _compute_confidence(self, hops: list[HopResult]) -> tuple[float, dict]:
        """
        Tính confidence từ 3 thành phần:
          relevance × 0.30 + support × 0.40 + utility × 0.30
        """
        if not hops:
            return 0.0, {"relevance": 0.0, "support": 0.0, "utility": 0.0}

        all_chunks = [c for h in hops for c in h.retrieved_chunks]
        rel_score = (
            sum(c.relevance_score for c in all_chunks) / len(all_chunks)
            if all_chunks else 0.0
        )
        # Phạt nặng nếu không có chunk nào relevant
        if all_chunks and not any(c.is_relevant for c in all_chunks):
            rel_score *= 0.3

        support_scores = [h.generation.support_score for h in hops]
        support_score = sum(support_scores) / len(support_scores)
        utility_score = max(h.generation.utility_score for h in hops)

        confidence = max(0.0, min(1.0,
            0.30 * rel_score + 0.40 * support_score + 0.30 * utility_score
        ))

        return round(confidence, 3), {
            "relevance": round(rel_score, 3),
            "support": round(support_score, 3),
            "utility": round(utility_score, 3),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        """Gọi Ollama LLM và trả về text."""
        result = self.llm.invoke(prompt)
        content = getattr(result, "content", result)
        if isinstance(content, list):
            return "\n".join(
                p if isinstance(p, str) else p.get("text", "") for p in content
            )
        return str(content)

    @staticmethod
    def _parse_json(text: str) -> dict:
        """
        Parse JSON từ LLM response.
        Thử json.loads thẳng trước, fallback regex nếu thất bại.
        """
        text = text.strip()
        text = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()

        # Bước 1: parse thẳng
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Bước 2: tìm JSON block đầu tiên bằng regex
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Không tìm thấy JSON hợp lệ trong: {text[:150]}")

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        """Ghép page_content của các chunks thành context string."""
        return "\n\n".join(
            getattr(c.document, "page_content", "")
            for c in chunks
            if getattr(c.document, "page_content", "")
        )