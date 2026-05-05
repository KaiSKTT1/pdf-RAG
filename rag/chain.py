"""Chain hỏi đáp: retrieval + re-ranking + prompt + sinh phản hồi + citations."""

from __future__ import annotations

import time

from langchain_ollama import ChatOllama

from config import (
    LLM_NUM_PREDICT,
    LLM_REPEAT_PENALTY,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    MAX_CONTEXT_CHARS,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    USE_SELF_RAG,
    SELF_RAG_CONFIDENCE_THRESHOLD,
    SELF_RAG_MAX_HOPS,
)
from .chain_parts.core_utils import (
    build_citations,
    extract_text_response,
    is_quota_error,
    retrieve_documents,
)
from .chain_parts.fallback import build_quota_fallback_answer
from .chain_parts.prompts import build_template, detect_language, is_code_request
from .chain_parts.text_processing import format_context, polish_answer_layout, trim_context
from .reranker import Reranker

# ── Self-RAG Advanced (v3) — batch relevance filter + multi-score confidence ─
from .self_rag1 import SelfRagAdvanced


class Chain:
    """Điều phối retrieval → re-ranking → sinh câu trả lời bằng LLM."""

    def __init__(self, retriever):
        """Khởi tạo LLM local qua Ollama, retriever và cross-encoder reranker."""
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=LLM_TEMPERATURE,
            top_p=LLM_TOP_P,
            repeat_penalty=LLM_REPEAT_PENALTY,
            num_predict=LLM_NUM_PREDICT,
        )
        self.retriever = retriever
        self.reranker = Reranker()


        # ── Self-RAG Advanced (v3) ───────────────────────────────────────────────
        if USE_SELF_RAG:
            self.self_rag_advanced = SelfRagAdvanced(
                retriever=self.retriever,
                max_hops=SELF_RAG_MAX_HOPS,
                relevance_threshold=0.45,
                support_threshold=SELF_RAG_CONFIDENCE_THRESHOLD,
            )
        else:
            self.self_rag_advanced = None

    # ── Helper methods (giữ lại, vẫn dùng bởi nhánh B) ──────────────────────

    def _retrieve_with_rerank(self, query: str) -> list:
        """Retrieve + rerank cho 1 query."""
        documents = retrieve_documents(self.retriever, query)
        documents, _ = self.reranker.rerank(query, documents)
        return documents

    def _generate_answer(
        self, question: str, documents: list, language: str, is_code_request_flag: bool
    ) -> str:
        """Sinh câu trả lời từ documents."""
        context = format_context(documents)
        context = trim_context(context, MAX_CONTEXT_CHARS)
        if not context.strip():
            return ""
        template = build_template(language, is_code_request_flag=is_code_request_flag)
        prompt = template.format(context=context, question=question)
        result = self.llm.invoke(prompt)
        answer = extract_text_response(result)
        if is_code_request_flag:
            answer = polish_answer_layout(answer)
        return answer

    # ── Main ask() ────────────────────────────────────────────────────────────

    def ask(self, question: str, return_sources: bool = False):
        """Trả lời câu hỏi, tuỳ chọn trả kèm citations và timing breakdown."""
        t0 = time.perf_counter()
        timings: dict[str, float | int | str] = {}

        language = detect_language(question)
        is_code_request_flag = is_code_request(question)

    
        # ═══════════════════════════════════════════════════════════════════════
        # NHÁNH A2: Self-RAG Advanced (v3)
        # Pipeline: Rewrite → Retrieve → Batch Filter → Generate → Eval → Follow-up
        # ═══════════════════════════════════════════════════════════════════════
        if self.self_rag_advanced is not None:
            t_adv = time.perf_counter()
            adv_result = self.self_rag_advanced.run(
                question=question,
                language=language,
            )
            timings["self_rag_seconds"] = round(time.perf_counter() - t_adv, 3)
            timings["self_rag"] = adv_result.to_dict()
            timings["self_rag_confidence"] = adv_result.confidence
            timings["self_rag_relevance"] = adv_result.relevance_score
            timings["self_rag_support"] = adv_result.support_score
            timings["self_rag_utility"] = adv_result.utility_score
            timings["retrieval_count"] = adv_result.retrieval_count
            timings["filtered_count"] = adv_result.filtered_count
            timings["total_seconds"] = round(time.perf_counter() - t0, 3)
            timings["rag_pipeline"] = "Self-RAG Advanced"

            answer = adv_result.final_answer
            if not answer:
                answer = (
                    "Tài liệu không có đủ thông tin để trả lời câu hỏi này."
                    if language == "vi"
                    else "The document does not contain enough information to answer this question."
                )

            if return_sources:
                return {
                    "answer": answer,
                    "citations": adv_result.citations,
                    "timings": timings,
                }
            return answer

        # ═══════════════════════════════════════════════════════════════════════
        # NHÁNH B: Pipeline gốc (không Self-RAG)
        # ═══════════════════════════════════════════════════════════════════════

        # ── Bi-encoder retrieval ──────────────────────────────────────────────
        t_retrieval_start = time.perf_counter()
        documents = retrieve_documents(self.retriever, question)
        timings["retrieval_seconds"] = round(time.perf_counter() - t_retrieval_start, 3)
        timings["retrieval_candidates"] = len(documents)

        # ── Cross-Encoder re-ranking ──────────────────────────────────────────
        t_rerank_start = time.perf_counter()
        documents, rerank_result = self.reranker.rerank(question, documents)
        timings["rerank_seconds"] = round(time.perf_counter() - t_rerank_start, 3)
        timings["rerank"] = rerank_result.to_dict()
        timings["rerank_scores"] = rerank_result.scores

        # ── Context formatting ────────────────────────────────────────────────
        t_context_start = time.perf_counter()
        context = format_context(documents)
        context = trim_context(context, MAX_CONTEXT_CHARS)
        timings["context_seconds"] = round(time.perf_counter() - t_context_start, 3)
        timings["context_chars"] = len(context)

        if not context.strip():
            if language == "vi":
                answer = "Tài liệu không có đủ thông tin để trả lời câu hỏi này."
            else:
                answer = "The document does not contain enough information to answer this question."

            timings["llm_seconds"] = 0.0
            timings["postprocess_seconds"] = 0.0
            timings["total_seconds"] = round(time.perf_counter() - t0, 3)

            if return_sources:
                return {"answer": answer, "citations": [], "timings": timings}
            return answer

        # ── Prompt building ───────────────────────────────────────────────────
        t_prompt_start = time.perf_counter()
        template = build_template(language, is_code_request_flag=is_code_request_flag)
        prompt = template.format(context=context, question=question)
        timings["prompt_seconds"] = round(time.perf_counter() - t_prompt_start, 3)
        timings["prompt_chars"] = len(prompt)

        # ── LLM inference ─────────────────────────────────────────────────────
        try:
            t_llm_start = time.perf_counter()
            result = self.llm.invoke(prompt)
            timings["llm_seconds"] = round(time.perf_counter() - t_llm_start, 3)

            t_post_start = time.perf_counter()
            answer = extract_text_response(result)
            if is_code_request_flag:
                answer = polish_answer_layout(answer)
            timings["postprocess_seconds"] = round(time.perf_counter() - t_post_start, 3)

        except Exception as exc:
            timings["llm_seconds"] = timings.get("llm_seconds", 0.0)
            if not is_quota_error(exc):
                raise

            t_fallback_start = time.perf_counter()
            answer = build_quota_fallback_answer(
                question=question,
                documents=documents,
                language=language,
                is_code_request_flag=is_code_request_flag,
            )
            timings["postprocess_seconds"] = round(time.perf_counter() - t_fallback_start, 3)
            timings["fallback"] = "retrieval_only"

        timings["total_seconds"] = round(time.perf_counter() - t0, 3)
        timings["rag_pipeline"] = "Standard + Rerank"

        if return_sources:
            return {
                "answer": answer,
                "citations": build_citations(documents),
                "timings": timings,
            }
        return answer