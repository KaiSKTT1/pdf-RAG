"""Bộ điều phối cấp cao cho ứng dụng Streamlit."""

import streamlit as st
from ui.styles import get_css
from ui.components.sidebar import Sidebar
from ui.components.main_area import MainArea


class StreamlitApp:
    """Ghép sidebar và main area thành trang ứng dụng hoàn chỉnh."""

    def run(self):
        """Cấu hình trang và hiển thị toàn bộ thành phần giao diện cấp cao."""
        st.set_page_config(
            page_title="PDF RAG Chatbot",
            page_icon="📄",
            layout="wide"
        )
        # Nạp CSS toàn cục ở mỗi lần Streamlit chạy lại.
        st.markdown(get_css(), unsafe_allow_html=True)

        # Hiển thị các vùng giao diện chính.
        Sidebar().render()
        MainArea().render()