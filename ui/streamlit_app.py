# ui/streamlit_app.py
import streamlit as st
from ui.styles import get_css
from ui.components.sidebar import Sidebar
from ui.components.main_area import MainArea

class StreamlitApp:
    def run(self):
        st.set_page_config(
            page_title="PDF RAG Chatbot",
            page_icon="📄",
            layout="wide"
        )
        # Apply color palette từ spec
        st.markdown(get_css(), unsafe_allow_html=True)

        # Render 2 component
        Sidebar().render()
        MainArea().render()