"""Lớp tiện ích tạo retriever từ FAISS với cấu hình tìm kiếm tập trung.

Lưu ý search_type:
  - "similarity" : lấy đúng k doc gần nhất, KHÔNG dùng fetch_k.
  - "mmr"         : lấy fetch_k ứng viên rồi chọn k đa dạng nhất, DÙNG fetch_k.

Khi bật reranker, ta cần FETCH_K > TOP_K để cross-encoder có đủ ứng viên
để lọc. Vì vậy search_type phải là "mmr" (hoặc similarity_score_threshold),
và k truyền vào phải là FETCH_K (cross-encoder sẽ giảm xuống TOP_K sau).
"""

from __future__ import annotations

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from config import SEARCH_TYPE, TOP_K, FETCH_K, USE_RERANKER, USE_HYBRID_SEARCH, HYBRID_WEIGHTS


def metadata_filter_predicate(metadata_filter: dict | None):
    """Tạo hàm predicate cho vectorstore filter theo metadata đã chọn."""
    if not metadata_filter:
        return None

    source_names = set(metadata_filter.get("source_names") or [])
    document_types = set(metadata_filter.get("document_types") or [])
    uploaded_dates = set(metadata_filter.get("uploaded_dates") or [])

    if not source_names and not document_types and not uploaded_dates:
        return None

    def _predicate(metadata: dict) -> bool:
        file_name = str(metadata.get("file_name") or metadata.get("source_name") or "")
        document_type = str(metadata.get("document_type") or "")
        uploaded_at = str(metadata.get("uploaded_at") or "")
        uploaded_date = uploaded_at[:10] if len(uploaded_at) >= 10 else uploaded_at

        if source_names and file_name not in source_names:
            return False
        if document_types and document_type not in document_types:
            return False
        if uploaded_dates and uploaded_date not in uploaded_dates:
            return False
        return True

    return _predicate


class Retriever:
    """Bao gói retriever để thống nhất tham số truy xuất trong toàn ứng dụng."""

    def __init__(self, vectorstore: FAISS, documents: list = None):
        """
        Khởi tạo retriever với search_type, k và fetch_k từ config.

        Khi USE_RERANKER=True:
          - Dùng search_type="mmr" để fetch_k có hiệu lực.
          - k=FETCH_K để cung cấp đủ ứng viên cho cross-encoder.
          - Cross-encoder (trong Chain) sẽ lọc xuống TOP_K sau.

        Khi USE_HYBRID_SEARCH=True:
          - Kết hợp vector retriever và BM25 retriever.
          - Cần truyền documents để tạo BM25.
        """
        if USE_HYBRID_SEARCH and documents:
            # Tạo hybrid retriever: vector + BM25
            vector_retriever = self._create_vector_retriever(vectorstore)
            bm25_retriever = BM25Retriever.from_documents(documents)
            bm25_retriever.k = TOP_K  # Đặt k cho BM25
            self.retriever = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=HYBRID_WEIGHTS
            )
        else:
            # Chỉ dùng vector retriever
            self.retriever = self._create_vector_retriever(vectorstore)

    def _create_vector_retriever(self, vectorstore: FAISS):
        """Tạo vector retriever từ FAISS với config."""
        if USE_RERANKER and FETCH_K > TOP_K:
            # MMR: lấy nhiều ứng viên, cross-encoder re-rank về TOP_K
            return vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": FETCH_K,       # Số doc trả về (= ứng viên cho CE)
                    "fetch_k": max(FETCH_K * 2, 20),  # Pool MMR nội bộ
                    "lambda_mult": 0.7, # 1.0 = thuần similarity, 0.0 = đa dạng tối đa
                },
            )
        else:
            # Không rerank: lấy đúng TOP_K, search_type theo config
            search_kwargs: dict = {"k": TOP_K}
            if SEARCH_TYPE == "mmr":
                search_kwargs["fetch_k"] = FETCH_K
            return vectorstore.as_retriever(
                search_type=SEARCH_TYPE,
                search_kwargs=search_kwargs,
            )

    @staticmethod
    def apply_metadata_filter_to_retriever(retriever, metadata_filter: dict | None):
        """Gắn predicate filter động vào retriever có hỗ trợ search_kwargs."""
        predicate = metadata_filter_predicate(metadata_filter)
        if not hasattr(retriever, "search_kwargs"):
            return
        search_kwargs = dict(getattr(retriever, "search_kwargs", {}) or {})
        if predicate is None:
            search_kwargs.pop("filter", None)
        else:
            search_kwargs["filter"] = predicate
        retriever.search_kwargs = search_kwargs

    def get_retriever(self):
        """Trả về retriever đã cấu hình sẵn cho chain sử dụng."""
        return self.retriever