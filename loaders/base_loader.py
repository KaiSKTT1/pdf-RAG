"""Khai báo interface trừu tượng cho các loader tài liệu trong pipeline RAG."""

from abc import ABC, abstractmethod


class BaseLoader(ABC):
    """Interface loader thống nhất đầu ra thành danh sách document đã chia chunk."""

    @abstractmethod
    def load_and_split(self, file_path: str, chunk_size: int, chunk_overlap: int) -> list:
        """Nạp file từ disk và trả về danh sách document đã chia đoạn."""
        raise NotImplementedError