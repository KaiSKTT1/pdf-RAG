"""Các panel thông tin/cấu hình hiển thị trong sidebar."""

import streamlit as st

from config import CHUNK_OVERLAP_OPTIONS, CHUNK_SIZE_OPTIONS, LLM_MODEL, TOP_K


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


def render_settings() -> None:
    """Hiển thị nhanh các tham số cấu hình truy xuất hiện tại."""
    st.header("⚙️ Cài đặt")
    st.markdown(
        f"""
        - **Chunk size (selected):** {st.session_state.get("chunk_size")}
        - **Chunk overlap (selected):** {st.session_state.get("chunk_overlap")}
        - **Top K chunks:** {TOP_K}
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