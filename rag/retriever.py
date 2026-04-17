"""Lớp tiện ích tạo retriever từ FAISS với cấu hình tìm kiếm tập trung."""

from langchain_community.vectorstores import FAISS
from config import SEARCH_TYPE, TOP_K, FETCH_K


class Retriever:
    """Bao gói retriever để thống nhất tham số truy xuất trong toàn ứng dụng."""

    def __init__(self, vectorstore: FAISS):
        """Khởi tạo retriever với search_type, k và fetch_k từ config."""
        self.retriever = vectorstore.as_retriever(
            search_type=SEARCH_TYPE,
            search_kwargs={
                "k": TOP_K,
                "fetch_k": FETCH_K
            }
        )

    def get_retriever(self):
        """Trả về retriever đã cấu hình sẵn cho chain sử dụng."""
        return self.retriever