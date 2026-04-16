# ui/components/sidebar.py
import streamlit as st
from config import (
    LLM_MODEL,
    CHUNK_SIZE_OPTIONS,
    CHUNK_OVERLAP_OPTIONS,
    TOP_K,
)
from ui.session_state import (
    ensure_app_session_state,
    normalize_chunk_selection,
    reset_chat_history_state,
    reset_vector_store_state,
)

class Sidebar:
    def render(self):
        self._ensure_session_state()
        with st.sidebar:
            self._instructions()
            st.divider()
            self._chunk_strategy_controls()
            st.divider()
            self._chat_history()
            st.divider()
            self._action_buttons()
            st.divider()
            self._settings()
            st.divider()
            self._model_config()

        # Render dialog outside sidebar for more consistent click behavior
        self._render_pending_dialogs()

    @staticmethod
    def _ensure_session_state():
        ensure_app_session_state()
        normalize_chunk_selection(CHUNK_SIZE_OPTIONS, CHUNK_OVERLAP_OPTIONS)

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

        options = self._build_history_options(history)
        selected_idx = self._resolve_selected_history_idx(len(options))

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

    @staticmethod
    def _build_history_options(history: list[dict]) -> list[str]:
        options = []
        for idx, item in enumerate(history, start=1):
            question = item.get("question", "")
            short_question = question if len(question) <= 60 else f"{question[:57]}..."
            options.append(f"{idx}. {short_question}")
        return options

    @staticmethod
    def _resolve_selected_history_idx(option_count: int) -> int:
        selected_idx = st.session_state.get("selected_history_idx")
        if selected_idx is None or selected_idx >= option_count:
            return option_count - 1
        return selected_idx

    def _chunk_strategy_controls(self):
        st.header("🧩 Chunk Strategy")
        st.selectbox(
            "Chunk size",
            options=CHUNK_SIZE_OPTIONS,
            key="chunk_size",
            help="Thử nghiệm các mức: 500, 1000, 1500, 2000",
        )
        st.selectbox(
            "Chunk overlap",
            options=CHUNK_OVERLAP_OPTIONS,
            key="chunk_overlap",
            help="Thử nghiệm các mức: 50, 100, 200",
        )

        has_active_chain = st.session_state.get("chain") is not None
        if not has_active_chain:
            st.caption("Tham số hiện chỉ là cấu hình chọn sẵn. Hãy xử lý tài liệu để áp dụng.")
            return

        active_size = st.session_state.get("chain_chunk_size")
        active_overlap = st.session_state.get("chain_chunk_overlap")
        selected_size = st.session_state.get("chunk_size")
        selected_overlap = st.session_state.get("chunk_overlap")

        if active_size != selected_size or active_overlap != selected_overlap:
            st.warning(
                "Bạn đã đổi chunk parameters. Nhấn 'Xử lý tài liệu' để áp dụng cấu hình mới."
            )
        else:
            st.caption(f"Đang áp dụng: chunk_size={active_size}, chunk_overlap={active_overlap}")

    @st.dialog("Xác nhận xóa lịch sử")
    def _confirm_clear_history(self):
        st.write("Bạn có chắc muốn xóa toàn bộ lịch sử chat trong session hiện tại?")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("Xóa", type="primary", key="confirm_clear_history"):
                reset_chat_history_state()
                st.session_state.show_clear_history_dialog = False
                st.toast("Đã xóa toàn bộ lịch sử chat.", icon="✅")
                st.rerun()
        with col_cancel:
            if st.button("Hủy", key="cancel_clear_history"):
                st.session_state.show_clear_history_dialog = False
                st.rerun()

    @st.dialog("Xác nhận xóa vector store")
    def _confirm_clear_vector_store(self):
        st.write("Bạn có chắc muốn xóa tài liệu đã upload và vector store hiện tại?")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("Xóa", type="primary", key="confirm_clear_vector_store"):
                reset_vector_store_state()
                st.session_state.show_clear_vector_store_dialog = False
                st.toast("Đã xóa vector store và reset tài liệu upload.", icon="✅")
                st.rerun()
        with col_cancel:
            if st.button("Hủy", key="cancel_clear_vector_store"):
                st.session_state.show_clear_vector_store_dialog = False
                st.rerun()

    def _action_buttons(self):
        st.header("🧹 Quản lý dữ liệu")
        history_count = self._history_count()
        has_vector_store = self._has_vector_store()

        st.caption(f"Lịch sử hiện có: {history_count} câu hỏi")
        if st.button(
            "Clear History",
            use_container_width=True,
            disabled=history_count == 0,
            help="Xóa toàn bộ câu hỏi và trả lời trong session hiện tại.",
        ):
            st.session_state.show_clear_history_dialog = True

        if st.button(
            "Clear Vector Store",
            use_container_width=True,
            disabled=not has_vector_store,
            help="Xóa tài liệu đã xử lý và dữ liệu truy xuất hiện tại.",
        ):
            st.session_state.show_clear_vector_store_dialog = True

    @staticmethod
    def _history_count() -> int:
        return len(st.session_state.get("chat_history", []))

    @staticmethod
    def _has_vector_store() -> bool:
        return (
            st.session_state.get("chain") is not None
            or bool(st.session_state.get("active_document_name"))
        )

    def _render_pending_dialogs(self):
        if st.session_state.get("show_clear_history_dialog"):
            self._confirm_clear_history()

        if st.session_state.get("show_clear_vector_store_dialog"):
            self._confirm_clear_vector_store()

    def _settings(self):
        st.header("⚙️ Cài đặt")
        st.markdown(f"""
        - **Chunk size (selected):** {st.session_state.get("chunk_size")}
        - **Chunk overlap (selected):** {st.session_state.get("chunk_overlap")}
        - **Top K chunks:** {TOP_K}
        """)

    def _model_config(self):
        st.header("🤖 Model")
        st.markdown(f"""
        - **LLM:** {LLM_MODEL}
        - **Embedding:** Multilingual MPNet
        - **Vector DB:** FAISS
        """)