"""Re-ranking với Cross-Encoder sau bước retrieval bi-encoder.

Luồng hoạt động:
  Bi-encoder (FAISS)  →  lấy FETCH_K ứng viên nhanh
  Cross-encoder       →  chấm lại từng cặp (query, chunk) chính xác hơn
  Kết quả             →  TOP_K chunk tốt nhất đưa vào LLM

Tại sao cần 2 tầng:
  - Bi-encoder encode query và doc riêng lẻ → dot-product → nhanh O(log n)
    nhưng không có cross-attention nên bỏ sót ngữ cảnh liên kết.
  - Cross-encoder encode cặp (query, doc) cùng lúc → full attention → chính xác
    hơn nhưng chậm O(n), chỉ chạy được trên tập nhỏ ứng viên.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional

from sentence_transformers import CrossEncoder

from config import (
    CROSS_ENCODER_MODEL,
    TOP_K,
    FETCH_K,
    RERANKER_BATCH_SIZE,
    RERANKER_MAX_LENGTH,
    USE_RERANKER,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RerankResult:
    """Kết quả re-ranking kèm metadata latency."""
    documents: list
    scores: list
    latency_ms: float = 0.0
    bi_encoder_count: int = 0
    reranked_count: int = 0
    skipped: bool = False

    def to_dict(self) -> dict:
        """Serialize sang dict để log/tracing, bỏ qua list documents."""
        return {
            "latency_ms": round(self.latency_ms, 1),
            "bi_encoder_count": self.bi_encoder_count,
            "reranked_count": self.reranked_count,
            "skipped": self.skipped,
        }


@dataclass
class LatencyStats:
    """So sánh latency bi-encoder vs cross-encoder."""
    bi_encoder_ms: float = 0.0
    cross_encoder_ms: float = 0.0
    total_ms: float = 0.0
    candidate_count: int = 0
    final_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Cross-Encoder Reranker
# ---------------------------------------------------------------------------

class CrossEncoderReranker:
    """Bọc cross-encoder model, cung cấp API re-ranking đơn giản."""

    def __init__(
        self,
        model_name: str = CROSS_ENCODER_MODEL,
        top_k: int = TOP_K,
        batch_size: int = RERANKER_BATCH_SIZE,
        max_length: int = RERANKER_MAX_LENGTH,
        device: Optional[str] = None,
    ):
        self.top_k = top_k
        self.batch_size = batch_size
        self._model: Optional[CrossEncoder] = None
        self._load_model(model_name, max_length, device)

    def _load_model(self, model_name: str, max_length: int, device: Optional[str]) -> None:
        try:
            kwargs = {"max_length": max_length}
            if device:
                kwargs["device"] = device
            self._model = CrossEncoder(model_name, **kwargs)
            logger.info("Cross-encoder loaded: %s", model_name)
        except Exception as exc:
            logger.warning("Không tải được cross-encoder (%s): %s", model_name, exc)
            self._model = None

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def rerank(self, query: str, documents: list, top_k: Optional[int] = None) -> RerankResult:
        """Re-rank documents theo query. Fallback về thứ tự gốc nếu model lỗi."""
        k = top_k if top_k is not None else self.top_k

        if not documents:
            return RerankResult(documents=[], scores=[], skipped=True)

        if not self.is_available:
            logger.warning("Cross-encoder không khả dụng, fallback về thứ tự bi-encoder.")
            return RerankResult(
                documents=documents[:k],
                scores=[0.0] * min(len(documents), k),
                bi_encoder_count=len(documents),
                reranked_count=min(len(documents), k),
                skipped=True,
            )

        t0 = time.perf_counter()

        pairs = [(query, self._get_text(doc)) for doc in documents]
        scores = self._predict_batched(pairs)

        ranked = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
        top_docs = [doc for _, doc in ranked[:k]]
        top_scores = [float(s) for s, _ in ranked[:k]]

        latency_ms = (time.perf_counter() - t0) * 1000
        logger.debug(
            "Re-ranked %d → %d docs in %.1f ms", len(documents), len(top_docs), latency_ms
        )

        return RerankResult(
            documents=top_docs,
            scores=top_scores,
            latency_ms=latency_ms,
            bi_encoder_count=len(documents),
            reranked_count=len(top_docs),
            skipped=False,
        )

    def _predict_batched(self, pairs: list) -> list:
        """Inference theo batch để tránh OOM với nhiều ứng viên."""
        all_scores: list[float] = []
        for i in range(0, len(pairs), self.batch_size):
            batch = pairs[i : i + self.batch_size]
            batch_scores = self._model.predict(batch)
            all_scores.extend(
                batch_scores.tolist() if hasattr(batch_scores, "tolist") else list(batch_scores)
            )
        return all_scores

    @staticmethod
    def _get_text(doc) -> str:
        return getattr(doc, "page_content", "") or ""


# ---------------------------------------------------------------------------
# Reranker — wrapper đơn giản dùng trong Chain
# ---------------------------------------------------------------------------

class Reranker:
    """
    Wrapper nhỏ dùng trong Chain.ask().

    - Nếu USE_RERANKER=True và model load được → dùng cross-encoder.
    - Ngược lại → trả nguyên danh sách bi-encoder (skipped=True).

    Chain.ask() chỉ cần gọi:
        documents, result = self.reranker.rerank(question, documents)
    """

    def __init__(self):
        if USE_RERANKER:
            self._ce = CrossEncoderReranker()
        else:
            self._ce = None

    def rerank(self, query: str, documents: list) -> tuple[list, RerankResult]:
        """
        Trả về (documents_sau_rerank, RerankResult).

        Chain.ask() nhận tuple này để log stats và dùng documents.
        """
        if self._ce is None or not self._ce.is_available:
            result = RerankResult(
                documents=documents,
                scores=[0.0] * len(documents),
                bi_encoder_count=len(documents),
                reranked_count=len(documents),
                skipped=True,
            )
            return documents, result

        result = self._ce.rerank(query, documents)
        return result.documents, result


# ---------------------------------------------------------------------------
# HybridRetriever: Bi-encoder + Cross-encoder trong 1 retriever
# (dùng khi muốn plug thẳng vào LangChain thay vì gọi tách bạch trong Chain)
# ---------------------------------------------------------------------------

class HybridRetriever:
    """
    Retriever 2 tầng, implement giao diện invoke() chuẩn LangChain.

    Tầng 1 — Bi-encoder (FAISS):
      Encode query và doc riêng lẻ, tìm kiếm ANN cực nhanh.
      Lấy FETCH_K ứng viên (nhiều hơn TOP_K để CE có đủ để lọc).

    Tầng 2 — Cross-encoder:
      Encode cặp (query, doc) cùng lúc với full attention.
      Chấm lại và giữ TOP_K chunk tốt nhất.
    """

    def __init__(self, bi_encoder_retriever, reranker: CrossEncoderReranker):
        self._bi_retriever = bi_encoder_retriever
        self._reranker = reranker
        self._last_stats: Optional[LatencyStats] = None

    @property
    def last_stats(self) -> Optional[LatencyStats]:
        return self._last_stats

    def invoke(self, query: str) -> list:
        """Giao diện chuẩn LangChain — thay thế trực tiếp Retriever.get_retriever()."""
        # Tầng 1: Bi-encoder lấy ứng viên
        t_bi = time.perf_counter()
        candidates = self._fetch_candidates(query)
        bi_ms = (time.perf_counter() - t_bi) * 1000

        # Tầng 2: Cross-encoder re-rank
        result = self._reranker.rerank(query, candidates)

        self._last_stats = LatencyStats(
            bi_encoder_ms=round(bi_ms, 1),
            cross_encoder_ms=round(result.latency_ms, 1),
            total_ms=round(bi_ms + result.latency_ms, 1),
            candidate_count=len(candidates),
            final_count=len(result.documents),
        )

        return result.documents

    def get_relevant_documents(self, query: str) -> list:
        """Tương thích LangChain cũ."""
        return self.invoke(query)

    def _fetch_candidates(self, query: str) -> list:
        if hasattr(self._bi_retriever, "invoke"):
            return self._bi_retriever.invoke(query) or []
        if hasattr(self._bi_retriever, "get_relevant_documents"):
            return self._bi_retriever.get_relevant_documents(query) or []
        raise AttributeError("bi_encoder_retriever không hỗ trợ invoke/get_relevant_documents")