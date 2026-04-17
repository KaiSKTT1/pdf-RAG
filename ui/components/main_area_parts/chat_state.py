"""Các tiện ích cập nhật trạng thái phiên chuyên biệt cho luồng chat."""

import streamlit as st

from config import CHUNK_OVERLAP, CHUNK_SIZE


def resolve_chunk_params() -> tuple[int, int]:
    """Lấy cấu hình chunk từ trạng thái phiên và ép kiểu về số nguyên."""
    chunk_size = int(st.session_state.get("chunk_size", CHUNK_SIZE))
    chunk_overlap = int(st.session_state.get("chunk_overlap", CHUNK_OVERLAP))
    return chunk_size, chunk_overlap


def record_user_question(question: str) -> int:
    """Ghi câu hỏi người dùng vào messages và chat_history, trả về index lịch sử."""
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.chat_history.append(
        {
            "question": question,
            "answer": "",
            "status": "pending",
        }
    )
    return len(st.session_state.chat_history) - 1


def record_assistant_response(
    history_index: int,
    question: str,
    content: str,
    status: str,
    citations: list | None = None,
) -> None:
    """Ghi phản hồi assistant và cập nhật trạng thái/nguồn cho lịch sử chat."""
    assistant_message = {
        "role": "assistant",
        "question": question,
        "content": content,
        "status": status,
    }
    if citations:
        assistant_message["citations"] = citations

    st.session_state.messages.append(assistant_message)
    st.session_state.chat_history[history_index]["answer"] = content
    st.session_state.chat_history[history_index]["status"] = status
    if citations:
        st.session_state.chat_history[history_index]["citations"] = citations