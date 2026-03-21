# ui/components/sidebar.py
import streamlit as st
from config import LLM_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K

class Sidebar:
    def render(self):
        with st.sidebar:
            self._instructions()
            st.divider()
            self._settings()
            st.divider()
            self._model_config()

    def _instructions(self):
        st.header("📖 Hướng dẫn")
        st.markdown("""
        1. Upload file PDF
        2. Nhấn **Xử lý PDF**
        3. Đặt câu hỏi về nội dung
        """)

    def _settings(self):
        st.header("⚙️ Cài đặt")
        st.markdown(f"""
        - **Chunk size:** {CHUNK_SIZE}
        - **Chunk overlap:** {CHUNK_OVERLAP}
        - **Top K chunks:** {TOP_K}
        """)

    def _model_config(self):
        st.header("🤖 Model")
        st.markdown(f"""
        - **LLM:** {LLM_MODEL}
        - **Embedding:** Multilingual MPNet
        - **Vector DB:** FAISS
        """)