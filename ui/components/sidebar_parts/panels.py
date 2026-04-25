"""Các panel thông tin/cấu hình hiển thị trong sidebar."""

import streamlit as st

from config import (
    CHUNK_OVERLAP_OPTIONS,
    CHUNK_SIZE_OPTIONS,
    LLM_MODEL,
    OCR_MODE_LABELS,
    OCR_MODE_OPTIONS,
    TOP_K,
)


def _ocr_mode_label(mode: str | None) -> str:
    """Trả về nhãn dễ đọc cho OCR mode."""
    if not mode:
        return "Chưa áp dụng"
    return OCR_MODE_LABELS.get(mode, mode)


def render_instructions() -> None:
    """Hiển thị hướng dẫn sử dụng nhanh cho người dùng cuối."""
    st.header("📖 Hướng dẫn")
    st.markdown(
        """
        1. Upload file PDF hoặc DOCX
        2. Nhấn **Xử lý tài liệu**
        3. Đặt câu hỏi về nội dung
        """
    )


def render_chunk_strategy_controls() -> None:
    """Hiển thị điều khiển chunk strategy và trạng thái cấu hình đang áp dụng."""
    st.header("🧩 Chunk Strategy")
    st.selectbox(
        "Chunk size",
        options=CHUNK_SIZE_OPTIONS,
        key="chunk_size",
        help="Thử nghiệm các mức: 500, 1000, 1500, 2000",
    )
    st.selectbox(
        "Chunk overlap",
        options=CHUNK_OVERLAP_OPTIONS,
        key="chunk_overlap",
        help="Thử nghiệm các mức: 50, 100, 200",
    )

    has_active_chain = st.session_state.get("chain") is not None
    if not has_active_chain:
        st.caption("Tham số hiện chỉ là cấu hình chọn sẵn. Hãy xử lý tài liệu để áp dụng.")
        return

    active_size = st.session_state.get("chain_chunk_size")
    active_overlap = st.session_state.get("chain_chunk_overlap")
    selected_size = st.session_state.get("chunk_size")
    selected_overlap = st.session_state.get("chunk_overlap")

    if active_size != selected_size or active_overlap != selected_overlap:
        st.warning(
            "Bạn đã đổi chunk parameters. Nhấn 'Xử lý tài liệu' để áp dụng cấu hình mới."
        )
    else:
        st.caption(f"Đang áp dụng: chunk_size={active_size}, chunk_overlap={active_overlap}")


def render_ocr_controls() -> None:
    """Hiển thị điều khiển OCR mode và trạng thái OCR đang áp dụng."""
    st.header("🔎 OCR")
    st.selectbox(
        "OCR mode",
        options=OCR_MODE_OPTIONS,
        key="ocr_mode",
        format_func=lambda mode: OCR_MODE_LABELS.get(mode, mode),
        help="off: tắt OCR, auto: OCR trang khó + vùng ảnh, force: OCR toàn bộ trang PDF.",
    )

    has_active_chain = st.session_state.get("chain") is not None
    if not has_active_chain:
        st.caption("OCR mode hiện chỉ là cấu hình chọn sẵn. Hãy xử lý tài liệu để áp dụng.")
        return

    active_mode = st.session_state.get("chain_ocr_mode")
    selected_mode = st.session_state.get("ocr_mode")

    if active_mode != selected_mode:
        st.warning("Bạn đã đổi OCR mode. Nhấn 'Xử lý tài liệu' để áp dụng cấu hình mới.")
        return

    stats = st.session_state.get("chain_ocr_stats") or {}
    attempted = int(stats.get("ocr_pages_attempted", 0) or 0)
    total_pages = int(stats.get("pages_total", 0) or 0)
    elapsed = float(stats.get("ocr_elapsed_seconds", 0.0) or 0.0)
    st.caption(
        f"Đang áp dụng: {_ocr_mode_label(active_mode)} | OCR trang: {attempted}/{total_pages} | "
        f"Thời gian OCR: {elapsed:.2f}s"
    )


def render_settings() -> None:
    """Hiển thị nhanh các tham số cấu hình truy xuất hiện tại."""
    st.header("⚙️ Cài đặt")
    st.markdown(
        f"""
        - **Chunk size (selected):** {st.session_state.get("chunk_size")}
        - **Chunk overlap (selected):** {st.session_state.get("chunk_overlap")}
        - **OCR mode (selected):** {_ocr_mode_label(st.session_state.get("ocr_mode"))}
        - **Top K chunks:** {TOP_K}
        """
    )

    stats = st.session_state.get("chain_ocr_stats") or {}
    if stats:
        st.markdown(
            f"""
            - **OCR pages attempted:** {int(stats.get("ocr_pages_attempted", 0) or 0)}
            - **OCR pages successful:** {int(stats.get("ocr_pages_successful", 0) or 0)}
            - **OCR image regions attempted:** {int(stats.get("ocr_image_regions_attempted", 0) or 0)}
            - **OCR image regions successful:** {int(stats.get("ocr_image_regions_successful", 0) or 0)}
            - **OCR elapsed (s):** {float(stats.get("ocr_elapsed_seconds", 0.0) or 0.0):.2f}
            """
        )


def render_model_config() -> None:
    """Hiển thị thông tin model/embedding/vector-db đang sử dụng."""
    st.header("🤖 Model")
    st.markdown(
        f"""
        - **LLM:** {LLM_MODEL}
        - **Embedding:** Multilingual MPNet
        - **Vector DB:** FAISS
        """
    )