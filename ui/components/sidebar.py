# ui/components/sidebar.py
import streamlit as st
from config import LLM_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K

class Sidebar:
    def render(self):
        self._ensure_session_state()
        with st.sidebar:
            self._instructions()
            st.divider()
            self._chat_history()
            st.divider()
            self._settings()
            st.divider()
            self._model_config()

    @staticmethod
    def _ensure_session_state():
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "selected_history_idx" not in st.session_state:
            st.session_state.selected_history_idx = None

    def _instructions(self):
        st.header("📖 Hướng dẫn")
        st.markdown("""
        1. Upload file PDF hoặc DOCX
        2. Nhấn **Xử lý tài liệu**
        3. Đặt câu hỏi về nội dung
        """)

    def _chat_history(self):
        st.header("🕘 Lịch sử chat")
        history = st.session_state.get("chat_history", [])

        if not history:
            st.caption("Chưa có câu hỏi nào trong session hiện tại.")
            return

        options = []
        for idx, item in enumerate(history, start=1):
            question = item.get("question", "")
            short_question = question if len(question) <= 60 else f"{question[:57]}..."
            options.append(f"{idx}. {short_question}")

        selected_idx = st.session_state.get("selected_history_idx")
        if selected_idx is None or selected_idx >= len(options):
            selected_idx = len(options) - 1

        selected_label = st.selectbox(
            "Chọn câu hỏi để xem lại",
            options=options,
            index=selected_idx,
        )
        selected_idx = options.index(selected_label)
        st.session_state.selected_history_idx = selected_idx

        selected_item = history[selected_idx]
        st.markdown("**Câu hỏi**")
        st.info(selected_item.get("question", ""))
        with st.expander("Xem câu trả lời", expanded=False):
            st.write(selected_item.get("answer", ""))

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