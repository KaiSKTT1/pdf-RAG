"""Hiển thị uploader và xử lý tạo chain từ tài liệu người dùng tải lên."""

import streamlit as st

from config import MAX_UPLOAD_FILE_MB, USE_SELF_RAG
from ui.session_state import reset_chat_history_state

from .chat_state import resolve_chunk_params, resolve_ocr_mode
from .utils import friendly_model_error, is_supported_document


def render_file_uploader(qa_service) -> None:
    """Hiển thị uploader, kiểm tra file, và khởi tạo chain khi người dùng xác nhận."""
    uploader_key = f"doc_uploader_{st.session_state.uploader_key_seed}"
    uploaded_files = st.file_uploader(
        "📂 Chọn file",
        type=["pdf", "docx"],
        key=uploader_key,
        accept_multiple_files=True,
    )

    if uploaded_files:
        selected_names = [file.name for file in uploaded_files]
        st.session_state.selected_document_name = ", ".join(selected_names)

        st.caption(f"Đã chọn {len(uploaded_files)} tài liệu: {', '.join(selected_names)}")
        if (
            st.session_state.active_document_name
            and st.session_state.active_document_name != st.session_state.selected_document_name
        ):
            st.caption(
                "Bạn đang dùng bộ tài liệu khác. Nhấn 'Xử lý tài liệu' để chuyển tập mới."
            )

        total_size_mb = 0.0
        for uploaded_file in uploaded_files:
            if not is_supported_document(uploaded_file):
                st.toast("Định dạng file không hợp lệ. Chỉ hỗ trợ file PDF hoặc DOCX.", icon="⚠️")
                return
            is_valid_size, file_size_mb = qa_service.validate_upload_size(
                uploaded_file,
                MAX_UPLOAD_FILE_MB,
            )
            total_size_mb += file_size_mb
            if not is_valid_size:
                st.toast(
                    f"File quá lớn ({file_size_mb:.2f} MB): {uploaded_file.name}. "
                    f"Vui lòng chọn file <= {MAX_UPLOAD_FILE_MB} MB.",
                    icon="❌",
                )
                return

        st.caption(
            f"Tổng dung lượng: {total_size_mb:.2f} MB | Giới hạn mỗi file: {MAX_UPLOAD_FILE_MB} MB"
        )

    if uploaded_files and st.button("⚡ Xử lý tài liệu"):
        try:
            chunk_size, chunk_overlap = resolve_chunk_params()
            ocr_mode = resolve_ocr_mode()

            with st.spinner("Đang xử lý tài liệu..."):
                st.session_state.chain = qa_service.build_chain_from_uploads(
                    uploaded_files,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    ocr_mode=ocr_mode,
                )
                document_catalog = qa_service.get_last_build_stats().get("documents", [])
                st.session_state.document_catalog = document_catalog
                st.session_state.active_document_name = ", ".join(
                    item.get("file_name", "") for item in document_catalog
                )
                st.session_state.chain_chunk_size = chunk_size
                st.session_state.chain_chunk_overlap = chunk_overlap
                st.session_state.chain_ocr_mode = ocr_mode
                if USE_SELF_RAG:
                    pipeline_label = "Self-RAG Advanced"
                elif USE_RERANKER:
                    pipeline_label = "Standard + Rerank"
                else:
                    pipeline_label = "Standard (No Rerank)"

                st.session_state.chain_rag_pipeline = pipeline_label
                build_stats = qa_service.get_last_build_stats()
                st.session_state.chain_ocr_stats = dict(build_stats.get("ocr", {}) or {})
                st.session_state.metadata_filters_reset_pending = True
                reset_chat_history_state()

            ocr_stats = st.session_state.get("chain_ocr_stats") or {}
            attempted = int(ocr_stats.get("ocr_pages_attempted", 0) or 0)
            elapsed = float(ocr_stats.get("ocr_elapsed_seconds", 0.0) or 0.0)
            st.toast(
                f"Xử lý xong {len(uploaded_files)} tài liệu | OCR: {ocr_mode} | "
                f"trang OCR: {attempted} | thời gian OCR: {elapsed:.2f}s",
                icon="✅",
            )
            # Sidebar render trước main area, nên cần rerun để filter metadata
            # được cập nhật ngay sau khi xử lý tài liệu.
            st.rerun()
        except Exception as exc:
            st.session_state.chain = None
            st.session_state.active_document_name = None
            st.session_state.document_catalog = []
            st.session_state.chain_chunk_size = None
            st.session_state.chain_chunk_overlap = None
            st.session_state.chain_ocr_mode = None
            st.session_state.chain_ocr_stats = None
            st.session_state.chain_rag_pipeline = None
            st.toast(friendly_model_error(exc), icon="❌")