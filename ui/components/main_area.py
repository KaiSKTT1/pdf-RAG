"""Vùng nội dung chính của ứng dụng: upload tài liệu và hỏi đáp."""

import streamlit as st

from services.rag_pdf_service import RagPdfService
from ui.components.main_area_parts.chat import render_chat
from ui.components.main_area_parts.upload import render_file_uploader
from ui.session_state import ensure_app_session_state, rebuild_chat_history_from_messages


class MainArea:
    """Lớp điều phối cho phần main area của giao diện Streamlit."""

    def __init__(self):
        self.qa_service = RagPdfService()

    def render(self):
        """Hiển thị tiêu đề, uploader và khu vực chat hỏi đáp."""
        st.title("📄 PDF/DOCX RAG Chatbot")
        st.caption("Upload PDF hoặc DOCX và đặt câu hỏi!")

        self._init_session_state()
        render_file_uploader(self.qa_service)
        render_chat(self.qa_service)

    @staticmethod
    def _init_session_state() -> None:
        """Đảm bảo trạng thái phiên đầy đủ trước khi hiển thị các thành phần con."""
        ensure_app_session_state()
        rebuild_chat_history_from_messages()