# ui/components/main_area.py
import streamlit as st
from services.rag_pdf_service import RagPdfService
from config import MAX_UPLOAD_FILE_MB

class MainArea:
    def __init__(self):
        self.qa_service = RagPdfService()

    def render(self):
        st.title("📄 PDF RAG Chatbot")
        st.caption("Upload PDF và đặt câu hỏi!")

        self._init_session_state()
        self._file_uploader()
        self._chat()

    def _init_session_state(self):
        if "chain" not in st.session_state:
            st.session_state.chain = None
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def _file_uploader(self):
        uploaded_file = st.file_uploader("📂 Chọn file PDF", type="pdf")

        if uploaded_file is not None:
            is_valid_size, file_size_mb = self.qa_service.validate_upload_size(
                uploaded_file,
                MAX_UPLOAD_FILE_MB,
            )
            st.caption(f"Dung lượng file: {file_size_mb:.2f} MB / tối đa {MAX_UPLOAD_FILE_MB} MB")
            if not is_valid_size:
                st.error(
                    f"❌ File quá lớn ({file_size_mb:.2f} MB). "
                    f"Vui lòng chọn file <= {MAX_UPLOAD_FILE_MB} MB."
                )
                return

        if uploaded_file and st.button("⚡ Xử lý PDF"):
            try:
                with st.spinner("Đang xử lý PDF..."):
                    st.session_state.chain = self.qa_service.build_chain(uploaded_file)
                    st.session_state.messages = []  # reset chat
                st.success("✓ Xử lý xong!")
            except Exception as exc:
                st.session_state.chain = None
                st.error(f"❌ Xử lý PDF thất bại: {exc}")

    def _chat(self):
        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Ô nhập câu hỏi
        if question := st.chat_input("Đặt câu hỏi về tài liệu..."):
            if st.session_state.chain is None:
                st.warning("⚠️ Vui lòng upload PDF trước!")
                return

            # Hiển thị câu hỏi
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)

            # Lấy câu trả lời
            with st.chat_message("assistant"):
                with st.spinner("Đang suy nghĩ..."):
                    answer = self.qa_service.ask(st.session_state.chain, question)
                    st.write(answer)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })