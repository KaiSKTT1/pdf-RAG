"""Lớp tiện ích tạo retriever từ FAISS với cấu hình tìm kiếm tập trung.

Lưu ý search_type:
  - "similarity" : lấy đúng k doc gần nhất, KHÔNG dùng fetch_k.
  - "mmr"         : lấy fetch_k ứng viên rồi chọn k đa dạng nhất, DÙNG fetch_k.

Khi bật reranker, ta cần FETCH_K > TOP_K để cross-encoder có đủ ứng viên
để lọc. Vì vậy search_type phải là "mmr" (hoặc similarity_score_threshold),
và k truyền vào phải là FETCH_K (cross-encoder sẽ giảm xuống TOP_K sau).
"""

from langchain_community.vectorstores import FAISS
from config import SEARCH_TYPE, TOP_K, FETCH_K, USE_RERANKER


class Retriever:
    """Bao gói retriever để thống nhất tham số truy xuất trong toàn ứng dụng."""

    def __init__(self, vectorstore: FAISS):
        """
        Khởi tạo retriever với search_type, k và fetch_k từ config.

        Khi USE_RERANKER=True:
          - Dùng search_type="mmr" để fetch_k có hiệu lực.
          - k=FETCH_K để cung cấp đủ ứng viên cho cross-encoder.
          - Cross-encoder (trong Chain) sẽ lọc xuống TOP_K sau.

        Khi USE_RERANKER=False:
          - Dùng search_type từ config, k=TOP_K như bình thường.
        """
        if USE_RERANKER and FETCH_K > TOP_K:
            # MMR: lấy nhiều ứng viên, cross-encoder re-rank về TOP_K
            self.retriever = vectorstore.as_retriever(
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
            self.retriever = vectorstore.as_retriever(
                search_type=SEARCH_TYPE,
                search_kwargs=search_kwargs,
            )

    def get_retriever(self):
        """Trả về retriever đã cấu hình sẵn cho chain sử dụng."""
        return self.retriever