"""Dịch vụ lớp ứng dụng cho luồng xử lý tài liệu PDF/DOCX và hỏi đáp RAG."""

import os
import tempfile
from typing import Any, Tuple

from config import CHUNK_SIZE, CHUNK_OVERLAP
from loaders.docx_loader import DOCXLoader
from loaders.pdf_loader import PDFLoader
from rag.embeddings import Embeddings
from rag.retriever import Retriever
from rag.chain import Chain


class RagPdfService:
    """Điều phối loader, embedding, retriever và chain cho luồng hỏi đáp."""

    def __init__(self):
        self.pdf_loader = PDFLoader()
        self.docx_loader = DOCXLoader()
        self.embeddings = Embeddings()

    @staticmethod
    def _detect_file_suffix(uploaded_file: Any) -> str:
        """Suy luận suffix chuẩn từ tên file hoặc MIME type upload."""
        file_name = (getattr(uploaded_file, "name", "") or "").lower()
        mime_type = (getattr(uploaded_file, "type", "") or "").lower()

        if file_name.endswith(".pdf") or mime_type == "application/pdf":
            return ".pdf"

        if file_name.endswith(".docx") or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return ".docx"

        raise ValueError("Định dạng file không hợp lệ. Chỉ hỗ trợ PDF hoặc DOCX")

    def validate_upload_size(self, uploaded_file: Any, max_size_mb: int) -> Tuple[bool, float]:
        """Kiểm tra kích thước file. Trả về (hợp_lệ, kích_thước_MB)."""
        file_size_mb = uploaded_file.size / (1024 * 1024)
        return file_size_mb <= max_size_mb, file_size_mb

    @staticmethod
    def validate_chunk_params(chunk_size: int, chunk_overlap: int) -> None:
        """Xác thực tham số chia chunk trước khi dựng pipeline."""
        if chunk_size <= 0:
            raise ValueError("chunk_size phải lớn hơn 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap không được âm")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap phải nhỏ hơn chunk_size")

    @staticmethod
    def _enrich_chunk_metadata(chunks: list, source_name: str) -> None:
        """Bổ sung metadata phục vụ giao diện citation (nguồn, trang, vị trí...)."""
        for idx, chunk in enumerate(chunks, start=1):
            metadata = dict(getattr(chunk, "metadata", {}) or {})

            metadata["chunk_id"] = idx
            metadata["source_name"] = source_name

            page = metadata.get("page")
            if isinstance(page, int):
                metadata["page_number"] = page + 1

            start_index = metadata.get("start_index")
            if isinstance(start_index, int):
                metadata["end_index"] = start_index + len(getattr(chunk, "page_content", "") or "")

            chunk.metadata = metadata

    def build_chain(
        self,
        uploaded_file: Any,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> Chain:
        """Tạo chain hỏi đáp từ file upload với cấu hình chunk tùy chỉnh."""
        tmp_path = None
        try:
            resolved_chunk_size = CHUNK_SIZE if chunk_size is None else chunk_size
            resolved_chunk_overlap = CHUNK_OVERLAP if chunk_overlap is None else chunk_overlap
            self.validate_chunk_params(resolved_chunk_size, resolved_chunk_overlap)

            suffix = self._detect_file_suffix(uploaded_file)

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            if suffix == ".pdf":
                chunks = self.pdf_loader.load_and_split(
                    tmp_path,
                    chunk_size=resolved_chunk_size,
                    chunk_overlap=resolved_chunk_overlap,
                )
            else:
                chunks = self.docx_loader.load_and_split(
                    tmp_path,
                    chunk_size=resolved_chunk_size,
                    chunk_overlap=resolved_chunk_overlap,
                )

            if not chunks:
                raise ValueError("Không thể trích xuất các đoạn văn bản từ tài liệu")

            # Metadata bổ sung giúp giao diện hiển thị citation chi tiết.
            self._enrich_chunk_metadata(chunks, source_name=uploaded_file.name)

            vectorstore = self.embeddings.create_vectorstore(chunks)
            retriever = Retriever(vectorstore)
            return Chain(retriever.get_retriever())
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def ask(self, chain: Chain, question: str, return_details: bool = False):
        """Trả lời câu hỏi từ chain đã tạo. Có thể trả về kèm citation details."""
        return chain.ask(question, return_sources=return_details)
