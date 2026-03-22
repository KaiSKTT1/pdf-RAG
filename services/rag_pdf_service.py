import os
import tempfile
from typing import Any, Tuple

from loaders.pdf_loader import PDFLoader
from rag.embeddings import Embeddings
from rag.retriever import Retriever
from rag.chain import Chain


class RagPdfService:
    """Service xử lý PDF và điều phối RAG pipeline."""

    def __init__(self):
        self.pdf_loader = PDFLoader()
        self.embeddings = Embeddings()

    def validate_upload_size(self, uploaded_file: Any, max_size_mb: int) -> Tuple[bool, float]:
        """Kiểm tra kích thước file. Trả về (hợp_lệ, kích_thước_MB)."""
        file_size_mb = uploaded_file.size / (1024 * 1024)
        return file_size_mb <= max_size_mb, file_size_mb

    def build_chain(self, uploaded_file: Any) -> Chain:
        """Tạo QA chain từ file PDF upload."""
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            chunks = self.pdf_loader.load_and_split(tmp_path)
            if not chunks:
                raise ValueError("Không thể trích xuất các đoạn văn bản từ PDF")

            vectorstore = self.embeddings.create_vectorstore(chunks)
            retriever = Retriever(vectorstore)
            return Chain(retriever.get_retriever())
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def ask(self, chain: Chain, question: str) -> str:
        """Trả lời câu hỏi từ chain đã tạo."""
        return chain.ask(question)
