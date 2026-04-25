"""Triển khai loader PDF với text native + EasyOCR tùy chọn."""

from __future__ import annotations

from time import perf_counter

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    OCR_GPU,
    OCR_LANGUAGES,
    OCR_MAX_PAGES_PER_DOC,
    OCR_MIN_NATIVE_TEXT_CHARS,
    OCR_MODE_DEFAULT,
    OCR_MODE_OPTIONS,
    OCR_RENDER_DPI,
)
from loaders.base_loader import BaseLoader
from loaders.easyocr_engine import EasyOCREngine
from loaders.pdf_ocr_pipeline import PdfOcrPipeline, new_ocr_stats


class PDFLoader(BaseLoader):
    """Nạp file PDF, có thể OCR bằng EasyOCR trước khi chia chunk."""

    def __init__(self, ocr_engine: EasyOCREngine | None = None, ocr_gpu: bool = OCR_GPU):
        self._ocr_pipeline = PdfOcrPipeline(ocr_engine=ocr_engine, ocr_gpu=ocr_gpu)
        self.last_load_stats: dict = {}

    def _resolve_ocr_mode(self, ocr_mode: str) -> str:
        """Chuẩn hóa và xác thực giá trị chế độ OCR."""
        resolved_mode = (ocr_mode or OCR_MODE_DEFAULT).strip().lower()
        if resolved_mode not in OCR_MODE_OPTIONS:
            raise ValueError(
                f"ocr_mode không hợp lệ: '{ocr_mode}'. Hỗ trợ: {', '.join(OCR_MODE_OPTIONS)}"
            )
        return resolved_mode

    @staticmethod
    def _build_load_stats(
        pages_total: int,
        chunks_total: int,
        ocr_mode: str,
        ocr_languages: list[str],
        ocr_stats: dict,
        elapsed_seconds: float,
    ) -> dict:
        """Tạo stats chuẩn cho lần load gần nhất để UI/service dùng thống nhất."""
        return {
            "pages_total": pages_total,
            "chunks_total": chunks_total,
            "ocr_mode": ocr_mode,
            "ocr_languages": ocr_languages,
            "ocr_pages_attempted": int(ocr_stats["ocr_pages_attempted"]),
            "ocr_pages_successful": int(ocr_stats["ocr_pages_successful"]),
            "ocr_pages_failed": int(ocr_stats["ocr_pages_failed"]),
            "ocr_image_regions_attempted": int(ocr_stats["ocr_image_regions_attempted"]),
            "ocr_image_regions_successful": int(ocr_stats["ocr_image_regions_successful"]),
            "ocr_image_regions_failed": int(ocr_stats["ocr_image_regions_failed"]),
            "ocr_pages_skipped_by_limit": int(ocr_stats["ocr_pages_skipped_by_limit"]),
            "ocr_elapsed_seconds": float(ocr_stats["ocr_elapsed_seconds"]),
            "elapsed_seconds": round(elapsed_seconds, 3),
        }

    def get_last_load_stats(self) -> dict:
        """Trả về bản sao thống kê lần load gần nhất."""
        return dict(self.last_load_stats)

    def load_and_split(
        self,
        file_path: str,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        ocr_mode: str = OCR_MODE_DEFAULT,
        ocr_languages: list[str] | None = None,
        ocr_min_native_text_chars: int = OCR_MIN_NATIVE_TEXT_CHARS,
        ocr_render_dpi: int = OCR_RENDER_DPI,
        ocr_max_pages: int = OCR_MAX_PAGES_PER_DOC,
    ) -> list:
        """Trả về document PDF đã xử lý OCR (nếu bật) và chia chunk."""
        started_at = perf_counter()
        resolved_ocr_mode = self._resolve_ocr_mode(ocr_mode)
        resolved_languages = list(ocr_languages or OCR_LANGUAGES)

        loader = PyPDFLoader(file_path)
        documents = loader.load()
        ocr_stats = new_ocr_stats()

        if not documents:
            self.last_load_stats = self._build_load_stats(
                pages_total=0,
                chunks_total=0,
                ocr_mode=resolved_ocr_mode,
                ocr_languages=resolved_languages,
                ocr_stats=ocr_stats,
                elapsed_seconds=perf_counter() - started_at,
            )
            return []

        if resolved_ocr_mode != "off":
            ocr_stats = self._ocr_pipeline.apply_to_documents(
                file_path=file_path,
                documents=documents,
                ocr_mode=resolved_ocr_mode,
                ocr_languages=resolved_languages,
                min_native_text_chars=ocr_min_native_text_chars,
                render_dpi=ocr_render_dpi,
                max_ocr_pages=ocr_max_pages,
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
        )
        chunks = splitter.split_documents(documents)

        self.last_load_stats = self._build_load_stats(
            pages_total=len(documents),
            chunks_total=len(chunks),
            ocr_mode=resolved_ocr_mode,
            ocr_languages=resolved_languages,
            ocr_stats=ocr_stats,
            elapsed_seconds=perf_counter() - started_at,
        )
        return chunks