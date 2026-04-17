"""Triển khai loader PDF sử dụng PyPDFLoader và bộ chia recursive."""

from loaders.base_loader import BaseLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP


class PDFLoader(BaseLoader):
    """Nạp file PDF và chia thành chunk để phục vụ bước embedding."""

    def load_and_split(
        self,
        file_path: str,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ) -> list:
        """Trả về document PDF đã chia chunk kèm metadata vị trí bắt đầu."""
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        if not documents:
            return []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
        )
        return splitter.split_documents(documents)