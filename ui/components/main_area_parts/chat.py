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

        rag_pipeline = st.session_state.get("chain_rag_pipeline")
        if rag_pipeline:
            st.caption(f"🧩 RAG pipeline: {rag_pipeline}")

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

    # ── Rerank stats (nhánh B — pipeline gốc) ────────────────────────────────
    rerank = timings.get("rerank")
    if rerank:
        bi_count = int(rerank.get("bi_encoder_count", 0) or 0)
        reranked_count = int(rerank.get("reranked_count", 0) or 0)
        rerank_ms = float(rerank.get("latency_ms", 0.0) or 0.0)
        skipped = bool(rerank.get("skipped", False))

        rerank_scores = timings.get("rerank_scores", [])
        scores_str = ""
        if rerank_scores:
            scores_str = " | scores: " + ", ".join(
                f"{s:.3f}" for s in rerank_scores[:reranked_count]
            )

        if skipped:
            st.caption(
                f"🔀 rerank=skipped | bi-encoder={bi_count} docs → top={reranked_count}{scores_str}"
            )
        else:
            st.caption(
                f"🔀 rerank={rerank_ms:.1f}ms | bi-encoder={bi_count} docs → top={reranked_count}{scores_str}"
            )

    # ── Self-RAG Advanced stats (nhánh A2) ───────────────────────────────────
    self_rag = timings.get("self_rag")
    if self_rag:
        sr_seconds = float(timings.get("self_rag_seconds", 0.0) or 0.0)
        confidence = float(self_rag.get("confidence", 0.0) or 0.0)
        hops = int(self_rag.get("hops", 1) or 1)
        final_query = str(self_rag.get("final_query", "") or "")

        # Điểm thành phần (Advanced v3 có 3 chiều)
        relevance_score = float(self_rag.get("relevance_score", 0.0) or 0.0)
        support_score = float(self_rag.get("support_score", 0.0) or 0.0)
        utility_score = float(self_rag.get("utility_score", 0.0) or 0.0)

        # Retrieval stats
        retrieval_count = int(self_rag.get("retrieval_count", 0) or 0)
        filtered_count = int(self_rag.get("filtered_count", 0) or 0)

        # Màu emoji theo confidence tổng hợp
        if confidence >= 0.7:
            conf_icon = "🟢"
        elif confidence >= 0.4:
            conf_icon = "🟡"
        else:
            conf_icon = "🔴"

        # Dòng 1: tổng quan
        caption = (
            f"🧠 self-rag-advanced={sr_seconds:.2f}s | {conf_icon} confidence={confidence:.3f} "
            f"| hops={hops} | retrieved={retrieval_count} → filtered={filtered_count}"
        )
        if final_query:
            preview = final_query[:80] + "..." if len(final_query) > 80 else final_query
            caption += f' | query="{preview}"'
        st.caption(caption)

        # Dòng 2: điểm 3 chiều
        st.caption(
            f"  📊 relevance={relevance_score:.3f} | support={support_score:.3f} | utility={utility_score:.3f}"
        )

        # Dòng 3+: chi tiết từng hop (nếu multi-hop)
        hop_details = self_rag.get("hop_details", [])
        if hop_details:
            for h in hop_details:
                sup = float(h.get("support_score", 0.0) or 0.0)
                util = float(h.get("utility_score", 0.0) or 0.0)
                # Dùng support_score để tô màu icon từng hop
                icon = "🟢" if sup >= 0.7 else ("🟡" if sup >= 0.4 else "🔴")
                chunks_retrieved = int(h.get("chunks_retrieved", 0) or 0)
                chunks_relevant = int(h.get("chunks_relevant", 0) or 0)
                follow_up = "✅" if h.get("follow_up_needed") else ""
                query_preview = str(h.get("query", ""))[:60]
                st.caption(
                    f"  ↳ hop {h.get('hop')}: {icon} support={sup:.2f} | utility={util:.2f} "
                    f"| chunks={chunks_retrieved}→{chunks_relevant} relevant "
                    f"{follow_up} | query=\"{query_preview}\""
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

                    if "rag_pipeline" in timings:
                        st.session_state.chain_rag_pipeline = timings["rag_pipeline"]

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