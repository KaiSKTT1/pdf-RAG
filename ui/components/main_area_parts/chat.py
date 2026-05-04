"""Hiển thị và điều phối luồng chat hỏi đáp trong main area."""

import streamlit as st

from config import TARGET_RESPONSE_SECONDS
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

        ocr_mode = st.session_state.get("chain_ocr_mode")
        ocr_stats = st.session_state.get("chain_ocr_stats") or {}
        attempted = int(ocr_stats.get("ocr_pages_attempted", 0) or 0)
        successful = int(ocr_stats.get("ocr_pages_successful", 0) or 0)
        elapsed = float(ocr_stats.get("ocr_elapsed_seconds", 0.0) or 0.0)
        if ocr_mode:
            st.caption(
                f"🔎 OCR đang áp dụng: mode={ocr_mode} | attempted={attempted} | "
                f"successful={successful} | elapsed={elapsed:.2f}s"
            )


def _parse_qa_response(response) -> tuple[str, list[dict], dict]:
    """Chuẩn hóa dữ liệu từ lời gọi ask của dịch vụ về dạng (câu_trả_lời, trích_dẫn, timing)."""
    if isinstance(response, dict):
        return (
            response.get("answer", ""),
            response.get("citations", []),
            dict(response.get("timings", {}) or {}),
        )
    return str(response), [], {}


def _render_latency_caption(timings: dict) -> None:
    """Hiển thị nhanh thời gian theo từng bước để theo dõi độ trễ câu trả lời."""
    if not timings:
        return

    total = float(timings.get("total_seconds", 0.0) or 0.0)
    retrieval = float(timings.get("retrieval_seconds", 0.0) or 0.0)
    llm = float(timings.get("llm_seconds", 0.0) or 0.0)
    context_chars = int(timings.get("context_chars", 0) or 0)
    prompt_chars = int(timings.get("prompt_chars", 0) or 0)
    fallback = timings.get("fallback")

    caption = (
        f"⏱️ total={total:.2f}s | retrieval={retrieval:.2f}s | "
        f"llm={llm:.2f}s | context={context_chars} chars | prompt={prompt_chars} chars"
    )
    if fallback:
        caption += " | fallback=retrieval_only"

    if total > TARGET_RESPONSE_SECONDS:
        caption += f" | vượt ngưỡng {TARGET_RESPONSE_SECONDS:.1f}s"

    st.caption(caption)

    rerank = timings.get("rerank")
    if rerank:
        bi_count = int(rerank.get("bi_encoder_count", 0) or 0)
        reranked_count = int(rerank.get("reranked_count", 0) or 0)
        rerank_ms = float(rerank.get("latency_ms", 0.0) or 0.0)
        skipped = bool(rerank.get("skipped", False))

        rerank_scores = timings.get("rerank_scores", [])
        scores_str = ""
        if rerank_scores:
            scores_str = " | scores: " + ", ".join(f"{s:.3f}" for s in rerank_scores[:reranked_count])

        if skipped:
            st.caption(f"🔀 rerank=skipped | bi-encoder={bi_count} docs → top={reranked_count}{scores_str}")
        else:
            st.caption(
                f"🔀 rerank={rerank_ms:.1f}ms | bi-encoder={bi_count} docs → top={reranked_count}{scores_str}"
            )


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
                    answer, citations, timings = _parse_qa_response(response)
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
                    _render_latency_caption(timings)
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