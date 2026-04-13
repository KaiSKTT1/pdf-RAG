# ui/components/main_area.py
import streamlit as st
from services.rag_pdf_service import RagPdfService
from config import MAX_UPLOAD_FILE_MB

class MainArea:
    def __init__(self):
        self.qa_service = RagPdfService()

    def render(self):
        st.title("📄 PDF/DOCX RAG Chatbot")
        st.caption("Upload PDF hoặc DOCX và đặt câu hỏi!")

        self._init_session_state()
        self._file_uploader()
        self._chat()

    def _init_session_state(self):
        if "chain" not in st.session_state:
            st.session_state.chain = None
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "selected_history_idx" not in st.session_state:
            st.session_state.selected_history_idx = None
        if "selected_document_name" not in st.session_state:
            st.session_state.selected_document_name = None
        if "active_document_name" not in st.session_state:
            st.session_state.active_document_name = None

    # hàm đó không dùng dữ liệu của object nên để staticmethod cho đúng ý nghĩa.

    @staticmethod
    def _is_supported_document(uploaded_file) -> bool:
        file_name = (uploaded_file.name or "").lower()
        mime_type = (uploaded_file.type or "").lower()
        if file_name.endswith(".pdf") or mime_type == "application/pdf":
            return True

        if file_name.endswith(".docx") or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return True

        return False

    # Hàm này chuyển đổi thống báo của gemini thành dữ liệu cho người dùng nhận thấy
    @staticmethod
    def _friendly_model_error(exc: Exception) -> str:
        error_text = str(exc)
        error_lower = error_text.lower()

        if "resourceexhausted" in error_lower or "quota" in error_lower or "429" in error_lower:
            return "Hết quota Gemini. Vui lòng kiểm tra lại hạn mức hoặc đổi API key/project."
        if "api key" in error_lower or "permission denied" in error_lower or "unauthorized" in error_lower:
            return "Gemini API key không hợp lệ hoặc chưa được cấp quyền."
        if "connect" in error_lower or "connection" in error_lower or "timeout" in error_lower:
            return "Không kết nối được tới dịch vụ mô hình. Vui lòng thử lại sau."

        return f"Lỗi khi gọi mô hình: {error_text}"

    def _file_uploader(self):
        uploaded_file = st.file_uploader("📂 Chọn file", type=["pdf", "docx"])

        if uploaded_file is not None:
            st.session_state.selected_document_name = uploaded_file.name

            if not self._is_supported_document(uploaded_file):
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

            is_valid_size, file_size_mb = self.qa_service.validate_upload_size(
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
                with st.spinner("Đang xử lý tài liệu..."):
                    st.session_state.chain = self.qa_service.build_chain(uploaded_file)
                    st.session_state.active_document_name = uploaded_file.name
                    st.session_state.messages = []  # reset chat
                    st.session_state.chat_history = []  # reset lịch sử Q&A
                    st.session_state.selected_history_idx = None
                st.toast(f"Xử lý tài liệu xong: {uploaded_file.name}", icon="✅")
            except Exception as exc:
                st.session_state.chain = None
                st.session_state.active_document_name = None
                st.toast(self._friendly_model_error(exc), icon="❌")

    def _chat(self):
        if st.session_state.active_document_name:
            st.caption(f"📌 Đang hỏi trên file: {st.session_state.active_document_name}")

        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Ô nhập câu hỏi
        if question := st.chat_input("Đặt câu hỏi về tài liệu..."):
            if st.session_state.chain is None:
                st.toast("Vui lòng upload PDF hoặc DOCX trước!", icon="⚠️")
                return

            # Hiển thị câu hỏi
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)

            # Lấy câu trả lời
            with st.chat_message("assistant"):
                with st.spinner("Đang suy nghĩ..."):
                    try:
                        answer = self.qa_service.ask(st.session_state.chain, question)
                        st.write(answer)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })
                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": answer,
                        })
                    except Exception as exc:
                        st.toast(self._friendly_model_error(exc), icon="❌")