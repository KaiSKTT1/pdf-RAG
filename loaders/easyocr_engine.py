"""Engine OCR dựa trên EasyOCR, dùng để nhận diện text từ ảnh trang PDF."""

from __future__ import annotations

from time import perf_counter
from typing import Sequence

import numpy as np


class EasyOCREngine:
    """Bọc EasyOCR reader để tái sử dụng model giữa nhiều lần OCR."""

    def __init__(self, gpu: bool = False):
        self.gpu = gpu
        self._readers: dict[tuple[str, ...], object] = {}

    def _get_reader(self, languages: Sequence[str]):
        """Khởi tạo/lấy lại reader theo cặp ngôn ngữ để giảm overhead."""
        key = tuple(languages)
        if key in self._readers:
            return self._readers[key]

        try:
            import easyocr
        except ImportError as exc:
            raise ImportError(
                "Chưa cài EasyOCR. Hãy chạy: pip install easyocr"
            ) from exc

        reader = easyocr.Reader(list(key), gpu=self.gpu)
        self._readers[key] = reader
        return reader

    @staticmethod
    def _normalize_lines(lines: Sequence[str]) -> str:
        """Chuẩn hóa đầu ra OCR thành text nhiều dòng gọn gàng."""
        normalized = [str(line).strip() for line in lines if str(line).strip()]
        return "\n".join(normalized).strip()

    def extract_text(self, image_array: np.ndarray, languages: Sequence[str]) -> tuple[str, float]:
        """Nhận diện text từ mảng ảnh và trả về (text, thời_gian_giây)."""
        if image_array is None or image_array.size == 0:
            return "", 0.0

        reader = self._get_reader(languages)
        started_at = perf_counter()
        # paragraph=False giúp giữ ngắt dòng tốt hơn cho ảnh chứa mã nguồn.
        lines = reader.readtext(image_array, detail=0, paragraph=False)
        elapsed = perf_counter() - started_at
        return self._normalize_lines(lines), elapsed
