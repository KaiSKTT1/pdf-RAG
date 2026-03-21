# ui/components/main_area.py
import streamlit as st
import tempfile
import os

from loaders.pdf_loader import PDFLoader
from rag.embeddings import Embeddings
from rag.retriever import Retriever
from rag.chain import Chain

class MainArea:
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

        if uploaded_file and st.button("⚡ Xử lý PDF"):
            with st.spinner("Đang xử lý PDF..."):
                st.session_state.chain = self._process_pdf(uploaded_file)
                st.session_state.messages = []  # reset chat
            st.success(f"✓ Xử lý xong!")

    def _process_pdf(self, uploaded_file) -> Chain:
        # Lưu file tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Gọi lần lượt các class
        chunks = PDFLoader().load_and_split(tmp_path)
        vectorstore = Embeddings().create_vectorstore(chunks)
        retriever = Retriever(vectorstore)
        chain = Chain(retriever.get_retriever())

        # Xóa file tạm
        os.unlink(tmp_path)
        return chain

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
                    answer = st.session_state.chain.ask(question)
                    st.write(answer)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })