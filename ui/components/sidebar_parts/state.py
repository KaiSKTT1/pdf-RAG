"""Tiện ích khởi tạo trạng thái riêng cho khu vực sidebar."""

from config import CHUNK_OVERLAP_OPTIONS, CHUNK_SIZE_OPTIONS
from ui.session_state import ensure_app_session_state, normalize_chunk_selection


def ensure_sidebar_state() -> None:
    """Đảm bảo các khóa trạng thái và lựa chọn chunk ở sidebar luôn hợp lệ."""
    ensure_app_session_state()
    normalize_chunk_selection(CHUNK_SIZE_OPTIONS, CHUNK_OVERLAP_OPTIONS)