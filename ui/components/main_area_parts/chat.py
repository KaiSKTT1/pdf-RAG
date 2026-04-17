"""Hiển thị và điều phối luồng chat hỏi đáp trong main area."""

import streamlit as st

from .chat_state import record_assistant_response, record_user_question
from .citation_view import render_assistant_message
from .utils import friendly_model_error, normalize_answer_text


def _render_active_document_caption() -> None:
    """Hiển thị thông tin tài liệu và cấu hình chunk đang được áp dụng."""
    if st.session_state.active_document_name:
        st.caption(f"📌 Đang hỏi trên file: {st.session_state.active_document_name}")
        active_chunk_size = st.session_state.get("chain_chunk_size")
        active_chunk_overlap = st.session_state.get("chain_chunk_overlap")
        if active_chunk_size and active_chunk_overlap is not None:
            st.caption(
                f"⚙️ Chunk đang áp dụng: size={active_chunk_size}, overlap={active_chunk_overlap}"
            )


def _parse_qa_response(response) -> tuple[str, list[dict]]:
    """Chuẩn hóa dữ liệu từ lời gọi ask của dịch vụ về dạng (câu_trả_lời, trích_dẫn)."""
    if isinstance(response, dict):
        return response.get("answer", ""), response.get("citations", [])
    return str(response), []


def _render_chat_messages() -> None:
    """Hiển thị toàn bộ tin nhắn đã lưu trong phiên theo thứ tự thời gian."""
    for msg_idx, message in enumerate(st.session_state.messages):
        role = message.get("role", "assistant")
        with st.chat_message(role):
            if role == "assistant":
                render_assistant_message(message, message_ref=f"msg_{msg_idx}")
            else:
                st.write(message.get("content", ""))


def render_chat(qa_service) -> None:
    """Điểm vào chính để hiển thị khu vực chat và xử lý câu hỏi mới."""
    _render_active_document_caption()
    _render_chat_messages()

    if question := st.chat_input("Đặt câu hỏi về tài liệu..."):
        if st.session_state.chain is None:
            st.toast("Vui lòng upload PDF hoặc DOCX trước!", icon="⚠️")
            return

        history_index = record_user_question(question)

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Đang suy nghĩ..."):
                try:
                    response = qa_service.ask(
                        st.session_state.chain,
                        question,
                        return_details=True,
                    )
                    answer, citations = _parse_qa_response(response)
                    answer = normalize_answer_text(answer)

                    record_assistant_response(
                        history_index,
                        question,
                        answer,
                        "answered",
                        citations,
                    )
                    render_assistant_message(
                        st.session_state.messages[-1],
                        message_ref=f"msg_{len(st.session_state.messages) - 1}",
                    )
                except Exception as exc:
                    error_message = friendly_model_error(exc)
                    st.toast(error_message, icon="❌")
                    record_assistant_response(
                        history_index,
                        question,
                        error_message,
                        "error",
                        [],
                    )
                    render_assistant_message(
                        st.session_state.messages[-1],
                        message_ref=f"msg_{len(st.session_state.messages) - 1}",
                    )