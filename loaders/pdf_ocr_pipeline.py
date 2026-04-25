"""Pipeline OCR cho PDF, tách riêng để giữ PDFLoader gọn gàng."""

from __future__ import annotations

import importlib
from typing import Any, TypedDict

import numpy as np

from loaders.easyocr_engine import EasyOCREngine


class OcrStats(TypedDict):
    """Cấu trúc thống kê OCR dùng xuyên suốt pipeline."""

    ocr_pages_attempted: int
    ocr_pages_successful: int
    ocr_pages_failed: int
    ocr_image_regions_attempted: int
    ocr_image_regions_successful: int
    ocr_image_regions_failed: int
    ocr_pages_skipped_by_limit: int
    ocr_elapsed_seconds: float


def new_ocr_stats() -> OcrStats:
    """Tạo bộ thống kê OCR mặc định."""
    return {
        "ocr_pages_attempted": 0,
        "ocr_pages_successful": 0,
        "ocr_pages_failed": 0,
        "ocr_image_regions_attempted": 0,
        "ocr_image_regions_successful": 0,
        "ocr_image_regions_failed": 0,
        "ocr_pages_skipped_by_limit": 0,
        "ocr_elapsed_seconds": 0.0,
    }


class PdfOcrPipeline:
    """Áp dụng OCR lên danh sách document PDF và cập nhật metadata."""

    def __init__(self, ocr_engine: EasyOCREngine | None = None, ocr_gpu: bool = False):
        self._ocr_engine = ocr_engine
        self._ocr_gpu = ocr_gpu

    def _ensure_ocr_engine(self) -> EasyOCREngine:
        """Khởi tạo lazy OCR engine để tránh overhead khi OCR tắt."""
        if self._ocr_engine is None:
            self._ocr_engine = EasyOCREngine(gpu=self._ocr_gpu)
        return self._ocr_engine

    @staticmethod
    def _import_fitz() -> Any:
        """Import PyMuPDF động để tránh lỗi môi trường thiếu phụ thuộc."""
        try:
            return importlib.import_module("fitz")
        except ModuleNotFoundError as exc:
            raise ImportError(
                "Chưa cài PyMuPDF. Hãy chạy: pip install pymupdf"
            ) from exc

    @staticmethod
    def _resolve_page_number(value: object, fallback: int, total_pages: int) -> int:
        """Chuẩn hóa page number về miền hợp lệ [0, total_pages-1]."""
        page_number = value if isinstance(value, int) else fallback
        return max(0, min(page_number, total_pages - 1))

    @staticmethod
    def _render_page_to_numpy(fitz: Any, pdf_doc: Any, page_number: int, dpi: int) -> np.ndarray:
        """Render toàn bộ trang PDF thành ảnh numpy cho OCR."""
        page = pdf_doc.load_page(page_number)
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height,
            pixmap.width,
            pixmap.n,
        )
        if pixmap.n >= 3:
            return image_array[:, :, :3]
        return image_array

    @staticmethod
    def _render_clip_to_numpy(
        fitz: Any,
        pdf_doc: Any,
        page_number: int,
        dpi: int,
        clip_rect: Any,
    ) -> np.ndarray:
        """Render một vùng clip trên trang PDF thành ảnh numpy cho OCR vùng."""
        page = pdf_doc.load_page(page_number)
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False, clip=clip_rect)
        image_array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height,
            pixmap.width,
            pixmap.n,
        )
        if pixmap.n >= 3:
            return image_array[:, :, :3]
        return image_array

    @staticmethod
    def _normalize_for_dedup(text: str) -> str:
        """Chuẩn hóa text để so sánh trùng lặp ổn định hơn."""
        return " ".join((text or "").split()).strip().lower()

    def _merge_native_and_ocr_text(self, native_text: str, ocr_texts: list[str]) -> str:
        """Ghép native text với OCR text và loại trùng lặp cơ bản."""
        base_text = (native_text or "").strip()
        merged_parts: list[str] = [base_text] if base_text else []

        normalized_seen = set()
        if base_text:
            normalized_seen.add(self._normalize_for_dedup(base_text))

        for ocr_text in ocr_texts:
            candidate = (ocr_text or "").strip()
            if not candidate:
                continue

            candidate_norm = self._normalize_for_dedup(candidate)
            if not candidate_norm:
                continue

            is_duplicate = False
            for seen_norm in normalized_seen:
                if candidate_norm in seen_norm or seen_norm in candidate_norm:
                    is_duplicate = True
                    break
            if is_duplicate:
                continue

            merged_parts.append(candidate)
            normalized_seen.add(candidate_norm)

        return "\n\n".join(part for part in merged_parts if part).strip()

    @staticmethod
    def _collect_image_rects(page: Any) -> list[Any]:
        """Lấy danh sách vùng ảnh (rect) trên trang, bỏ vùng quá nhỏ/trùng."""
        image_rects = []
        seen = set()

        for image_info in page.get_images(full=True):
            xref = image_info[0]
            try:
                rects = page.get_image_rects(xref)
            except Exception:
                rects = []

            for rect in rects:
                if rect.is_empty:
                    continue
                if rect.width * rect.height < 800:
                    continue

                key = (
                    round(rect.x0, 1),
                    round(rect.y0, 1),
                    round(rect.x1, 1),
                    round(rect.y1, 1),
                )
                if key in seen:
                    continue

                seen.add(key)
                image_rects.append(rect)

        return image_rects

    @staticmethod
    def _update_document_metadata(
        document: Any,
        metadata: dict,
        ocr_mode: str,
        page_attempted: bool,
        page_elapsed: float,
        has_images: bool,
        image_rects_count: int,
        page_ocr_fragments: list[str],
        page_error_messages: list[str],
        skipped_by_limit: bool = False,
    ) -> None:
        """Cập nhật metadata OCR thống nhất cho một document trang."""
        metadata["ocr_engine"] = "easyocr"
        metadata["ocr_mode"] = ocr_mode
        metadata["ocr_page_attempted"] = page_attempted
        metadata["ocr_skipped_by_limit"] = skipped_by_limit
        metadata["ocr_elapsed_seconds"] = round(page_elapsed, 4)
        metadata["ocr_has_images"] = has_images
        metadata["ocr_image_regions_attempted"] = image_rects_count if ocr_mode == "auto" else 0
        metadata["ocr_text_chars"] = sum(len(text) for text in page_ocr_fragments)
        if page_error_messages:
            metadata["ocr_error"] = " | ".join(page_error_messages[:2])
        document.metadata = metadata

    def apply_to_documents(
        self,
        file_path: str,
        documents: list[Any],
        ocr_mode: str,
        ocr_languages: list[str],
        min_native_text_chars: int,
        render_dpi: int,
        max_ocr_pages: int,
    ) -> OcrStats:
        """OCR theo trang và cập nhật page_content/metadata theo mode được chọn."""
        fitz = self._import_fitz()
        engine = self._ensure_ocr_engine()
        stats = new_ocr_stats()
        resolved_max_ocr_pages = max(0, int(max_ocr_pages))

        with fitz.open(file_path) as pdf_doc:
            total_pages = pdf_doc.page_count
            if total_pages == 0:
                return stats

            for page_idx, document in enumerate(documents):
                metadata = dict(getattr(document, "metadata", {}) or {})

                if resolved_max_ocr_pages > 0 and stats["ocr_pages_attempted"] >= resolved_max_ocr_pages:
                    stats["ocr_pages_skipped_by_limit"] += 1
                    self._update_document_metadata(
                        document=document,
                        metadata=metadata,
                        ocr_mode=ocr_mode,
                        page_attempted=False,
                        page_elapsed=0.0,
                        has_images=False,
                        image_rects_count=0,
                        page_ocr_fragments=[],
                        page_error_messages=[],
                        skipped_by_limit=True,
                    )
                    continue

                page_number = self._resolve_page_number(
                    metadata.get("page", page_idx),
                    page_idx,
                    total_pages,
                )

                page = pdf_doc.load_page(page_number)
                image_rects = self._collect_image_rects(page) if ocr_mode == "auto" else []
                has_images = len(image_rects) > 0

                native_text = str(getattr(document, "page_content", "") or "")
                should_full_page_ocr = ocr_mode == "force" or (
                    ocr_mode == "auto" and len(native_text.strip()) < min_native_text_chars
                )

                page_attempted = False
                page_success = False
                page_elapsed = 0.0
                page_error_messages: list[str] = []
                page_ocr_fragments: list[str] = []

                if should_full_page_ocr:
                    page_attempted = True
                    try:
                        image_array = self._render_page_to_numpy(
                            fitz,
                            pdf_doc,
                            page_number,
                            dpi=render_dpi,
                        )
                        ocr_text, elapsed = engine.extract_text(image_array, ocr_languages)
                        page_elapsed += elapsed

                        ocr_text = ocr_text.strip()
                        if ocr_text:
                            page_success = True
                            if ocr_mode == "force":
                                document.page_content = ocr_text
                            else:
                                merged_text = self._merge_native_and_ocr_text(native_text, [ocr_text])
                                document.page_content = merged_text if merged_text else native_text
                            page_ocr_fragments.append(ocr_text)
                    except Exception as exc:
                        page_error_messages.append(str(exc))

                if ocr_mode == "auto" and has_images and not should_full_page_ocr:
                    for rect in image_rects:
                        stats["ocr_image_regions_attempted"] += 1
                        page_attempted = True
                        try:
                            image_array = self._render_clip_to_numpy(
                                fitz,
                                pdf_doc,
                                page_number,
                                dpi=render_dpi,
                                clip_rect=rect,
                            )
                            ocr_text, elapsed = engine.extract_text(image_array, ocr_languages)
                            page_elapsed += elapsed

                            ocr_text = ocr_text.strip()
                            if ocr_text:
                                page_success = True
                                page_ocr_fragments.append(ocr_text)
                                stats["ocr_image_regions_successful"] += 1
                            else:
                                stats["ocr_image_regions_failed"] += 1
                        except Exception as exc:
                            stats["ocr_image_regions_failed"] += 1
                            page_error_messages.append(str(exc))

                    if page_ocr_fragments:
                        merged_text = self._merge_native_and_ocr_text(native_text, page_ocr_fragments)
                        document.page_content = merged_text if merged_text else native_text

                if page_attempted:
                    stats["ocr_pages_attempted"] += 1
                    if page_success:
                        stats["ocr_pages_successful"] += 1
                    else:
                        stats["ocr_pages_failed"] += 1

                stats["ocr_elapsed_seconds"] += page_elapsed
                self._update_document_metadata(
                    document=document,
                    metadata=metadata,
                    ocr_mode=ocr_mode,
                    page_attempted=page_attempted,
                    page_elapsed=page_elapsed,
                    has_images=has_images,
                    image_rects_count=len(image_rects),
                    page_ocr_fragments=page_ocr_fragments,
                    page_error_messages=page_error_messages,
                    skipped_by_limit=False,
                )

        stats["ocr_elapsed_seconds"] = round(stats["ocr_elapsed_seconds"], 3)
        return stats
