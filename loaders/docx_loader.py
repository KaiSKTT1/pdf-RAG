"""Triển khai loader DOCX sử dụng Docx2txtLoader và recursive splitter."""

from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE
from loaders.base_loader import BaseLoader


class DOCXLoader(BaseLoader):
    """Nạp file DOCX và chia chunk để đưa vào pipeline embedding/retrieval."""

    def load_and_split(
        self,
        file_path: str,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ) -> list:
        """Trả về document DOCX đã chia chunk kèm metadata vị trí bắt đầu."""
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        if not documents:
            return []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
        )
        return splitter.split_documents(documents)
