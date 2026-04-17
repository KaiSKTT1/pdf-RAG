"""Các thao tác quản trị dữ liệu trong sidebar (clear history/vector store)."""

import streamlit as st

from ui.session_state import reset_chat_history_state, reset_vector_store_state


def render_action_buttons() -> None:
    """Hiển thị nút thao tác xóa dữ liệu và bật cờ hiển thị dialog xác nhận."""
    st.header("🧹 Quản lý dữ liệu")
    history_count = _history_count()
    has_vector_store = _has_vector_store()

    st.caption(f"Lịch sử hiện có: {history_count} câu hỏi")
    if st.button(
        "Clear History",
        use_container_width=True,
        disabled=history_count == 0,
        help="Xóa toàn bộ câu hỏi và trả lời trong session hiện tại.",
    ):
        st.session_state.show_clear_history_dialog = True

    if st.button(
        "Clear Vector Store",
        use_container_width=True,
        disabled=not has_vector_store,
        help="Xóa tài liệu đã xử lý và dữ liệu truy xuất hiện tại.",
    ):
        st.session_state.show_clear_vector_store_dialog = True


@st.dialog("Xác nhận xóa lịch sử")
def _confirm_clear_history() -> None:
    """Dialog xác nhận trước khi xóa toàn bộ lịch sử chat session."""
    st.write("Bạn có chắc muốn xóa toàn bộ lịch sử chat trong session hiện tại?")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Xóa", type="primary", key="confirm_clear_history"):
            reset_chat_history_state()
            st.session_state.show_clear_history_dialog = False
            st.toast("Đã xóa toàn bộ lịch sử chat.", icon="✅")
            st.rerun()
    with col_cancel:
        if st.button("Hủy", key="cancel_clear_history"):
            st.session_state.show_clear_history_dialog = False
            st.rerun()


@st.dialog("Xác nhận xóa vector store")
def _confirm_clear_vector_store() -> None:
    """Hộp thoại xác nhận trước khi đặt lại tài liệu và vector store hiện tại."""
    st.write("Bạn có chắc muốn xóa tài liệu đã upload và vector store hiện tại?")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Xóa", type="primary", key="confirm_clear_vector_store"):
            reset_vector_store_state()
            st.session_state.show_clear_vector_store_dialog = False
            st.toast("Đã xóa vector store và reset tài liệu upload.", icon="✅")
            st.rerun()
    with col_cancel:
        if st.button("Hủy", key="cancel_clear_vector_store"):
            st.session_state.show_clear_vector_store_dialog = False
            st.rerun()


def render_pending_dialogs() -> None:
    """Hiển thị các hộp thoại đang chờ xử lý theo cờ trong trạng thái phiên."""
    if st.session_state.get("show_clear_history_dialog"):
        _confirm_clear_history()

    if st.session_state.get("show_clear_vector_store_dialog"):
        _confirm_clear_vector_store()


def _history_count() -> int:
    """Trả về số câu hỏi đã lưu trong lịch sử chat hiện tại."""
    return len(st.session_state.get("chat_history", []))


def _has_vector_store() -> bool:
    """Xác định liệu session hiện có dữ liệu truy xuất cần được xóa hay không."""
    return (
        st.session_state.get("chain") is not None
        or bool(st.session_state.get("active_document_name"))
    )