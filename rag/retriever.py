"""Lớp tiện ích tạo retriever từ FAISS với cấu hình tìm kiếm tập trung.

Lưu ý search_type:
  - "similarity" : lấy đúng k doc gần nhất, KHÔNG dùng fetch_k.
  - "mmr"         : lấy fetch_k ứng viên rồi chọn k đa dạng nhất, DÙNG fetch_k.

Khi bật reranker, ta cần FETCH_K > TOP_K để cross-encoder có đủ ứng viên
để lọc. Vì vậy search_type phải là "mmr" (hoặc similarity_score_threshold),
và k truyền vào phải là FETCH_K (cross-encoder sẽ giảm xuống TOP_K sau).
"""

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from config import SEARCH_TYPE, TOP_K, FETCH_K, USE_RERANKER, USE_HYBRID_SEARCH, HYBRID_WEIGHTS


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

    def get_retriever(self):
        """Trả về retriever đã cấu hình sẵn cho chain sử dụng."""
        return self.retriever