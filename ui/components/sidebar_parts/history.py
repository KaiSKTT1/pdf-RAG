"""Hiển thị và quản lý thao tác xem lại lịch sử chat trong sidebar."""

import streamlit as st


def render_chat_history() -> None:
    """Hiển thị danh sách câu hỏi đã hỏi và cho phép xem lại câu trả lời tương ứng."""
    st.header("🕘 Lịch sử chat")
    history = st.session_state.get("chat_history", [])

    if not history:
        st.caption("Chưa có câu hỏi nào trong session hiện tại.")
        return

    options = _build_history_options(history)
    selected_idx = _resolve_selected_history_idx(len(options))

    selected_label = st.selectbox(
        "Chọn câu hỏi để xem lại",
        options=options,
        index=selected_idx,
    )
    selected_idx = options.index(selected_label)
    st.session_state.selected_history_idx = selected_idx

    selected_item = history[selected_idx]
    st.markdown("**Câu hỏi**")
    st.info(selected_item.get("question", ""))
    with st.expander("Xem câu trả lời", expanded=False):
        st.write(selected_item.get("answer", ""))


def _build_history_options(history: list[dict]) -> list[str]:
    """Tạo danh sách nhãn ngắn gọn cho selectbox lịch sử câu hỏi."""
    options = []
    for idx, item in enumerate(history, start=1):
        question = item.get("question", "")
        short_question = question if len(question) <= 60 else f"{question[:57]}..."
        options.append(f"{idx}. {short_question}")
    return options


def _resolve_selected_history_idx(option_count: int) -> int:
    """Chuẩn hóa index đang chọn để không vượt phạm vi option hiện tại."""
    selected_idx = st.session_state.get("selected_history_idx")
    if selected_idx is None or selected_idx >= option_count:
        return option_count - 1
    return selected_idx