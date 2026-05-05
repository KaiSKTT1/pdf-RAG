"""Hiển thị uploader và xử lý tạo chain từ tài liệu người dùng tải lên."""

import streamlit as st

from config import MAX_UPLOAD_FILE_MB, USE_SELF_RAG
from ui.session_state import reset_chat_history_state

from .chat_state import resolve_chunk_params, resolve_ocr_mode
from .utils import friendly_model_error, is_supported_document


def render_file_uploader(qa_service) -> None:
    """Hiển thị uploader, kiểm tra file, và khởi tạo chain khi người dùng xác nhận."""
    uploader_key = f"doc_uploader_{st.session_state.uploader_key_seed}"
    uploaded_file = st.file_uploader("📂 Chọn file", type=["pdf", "docx"], key=uploader_key)

    if uploaded_file is not None:
        st.session_state.selected_document_name = uploaded_file.name

        if not is_supported_document(uploaded_file):
            st.toast("Định dạng file không hợp lệ. Chỉ hỗ trợ file PDF hoặc DOCX.", icon="⚠️")
            return

        st.caption(f"File đã chọn: {uploaded_file.name}")
        if (
            st.session_state.active_document_name
            and st.session_state.active_document_name != uploaded_file.name
        ):
            st.caption(
                f"File đang dùng hiện tại: {st.session_state.active_document_name}. "
                "Nhấn 'Xử lý tài liệu' để chuyển sang file mới."
            )

        is_valid_size, file_size_mb = qa_service.validate_upload_size(
            uploaded_file,
            MAX_UPLOAD_FILE_MB,
        )
        st.caption(f"Dung lượng file: {file_size_mb:.2f} MB / tối đa {MAX_UPLOAD_FILE_MB} MB")
        if not is_valid_size:
            st.toast(
                f"File quá lớn ({file_size_mb:.2f} MB). Vui lòng chọn file <= {MAX_UPLOAD_FILE_MB} MB.",
                icon="❌",
            )
            return

    if uploaded_file and st.button("⚡ Xử lý tài liệu"):
        try:
            chunk_size, chunk_overlap = resolve_chunk_params()
            ocr_mode = resolve_ocr_mode()

            with st.spinner("Đang xử lý tài liệu..."):
                st.session_state.chain = qa_service.build_chain(
                    uploaded_file,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    ocr_mode=ocr_mode,
                )
                st.session_state.active_document_name = uploaded_file.name
                st.session_state.chain_chunk_size = chunk_size
                st.session_state.chain_chunk_overlap = chunk_overlap
                st.session_state.chain_ocr_mode = ocr_mode
                st.session_state.chain_rag_pipeline = "Self-RAG Advanced" if USE_SELF_RAG else "Standard + Rerank"
                build_stats = qa_service.get_last_build_stats()
                st.session_state.chain_ocr_stats = dict(build_stats.get("ocr", {}) or {})
                reset_chat_history_state()

            ocr_stats = st.session_state.get("chain_ocr_stats") or {}
            attempted = int(ocr_stats.get("ocr_pages_attempted", 0) or 0)
            elapsed = float(ocr_stats.get("ocr_elapsed_seconds", 0.0) or 0.0)
            st.toast(
                f"Xử lý tài liệu xong: {uploaded_file.name} | OCR: {ocr_mode} | "
                f"trang OCR: {attempted} | thời gian OCR: {elapsed:.2f}s",
                icon="✅",
            )
        except Exception as exc:
            st.session_state.chain = None
            st.session_state.active_document_name = None
            st.session_state.chain_chunk_size = None
            st.session_state.chain_chunk_overlap = None
            st.session_state.chain_ocr_mode = None
            st.session_state.chain_ocr_stats = None
            st.session_state.chain_rag_pipeline = None
            st.toast(friendly_model_error(exc), icon="❌")