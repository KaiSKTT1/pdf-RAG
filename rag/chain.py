"""Chain hỏi đáp: retrieval + prompt + sinh phản hồi + đóng gói citations."""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_MODEL, GEMINI_API_KEY, LLM_TEMPERATURE


class Chain:
    """Điều phối quy trình truy xuất ngữ cảnh và sinh câu trả lời bằng LLM."""

    def __init__(self, retriever):
        """Khởi tạo LLM Gemini và gắn retriever đã được chuẩn bị trước."""
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=LLM_TEMPERATURE,
            google_api_key=GEMINI_API_KEY
        )
        self.retriever = retriever

    def _detect_language(self, text: str) -> str:
        """Phát hiện nhanh ngôn ngữ câu hỏi để chọn prompt vi/en phù hợp."""
        vietnamese_chars = 'àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ'
        is_vietnamese = any(char in text.lower() for char in vietnamese_chars)
        return "vi" if is_vietnamese else "en"

    def _build_template(self, language: str) -> str:
        """Trả về prompt template theo ngôn ngữ đầu vào."""
        if language == "vi":
            return """Bạn là trợ lý AI chuyên phân tích tài liệu. Nhiệm vụ của bạn là trả lời câu hỏi DỰA HOÀN TOÀN vào ngữ cảnh được cung cấp.

NGUYÊN TẮC BẮT BUỘC:
- Chỉ sử dụng thông tin có trong ngữ cảnh bên dưới
- Nếu ngữ cảnh không đủ thông tin, hãy nói: "Tài liệu không có đủ thông tin để trả lời câu hỏi này."
- KHÔNG tự bịa thêm thông tin ngoài ngữ cảnh
- Trả lời bằng tiếng Việt, rõ ràng và có cấu trúc
- Định dạng đầu ra là văn bản thuần, xuống dòng mạch lạc; KHÔNG dùng markdown như *, **, #, -, ```

NGỮ CẢNH:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""

        return """You are an AI assistant specialized in document analysis. Your task is to answer questions STRICTLY based on the provided context.

MANDATORY RULES:
- Only use information from the context below
- If the context lacks sufficient information, respond: "The document does not contain enough information to answer this question."
- Do NOT fabricate or add information beyond the context
- Be clear, structured, and thorough in your response
- Output plain text with clear line breaks; do NOT use markdown symbols like *, **, #, -, ```

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    def _retrieve_documents(self, question: str) -> list:
        """Lấy tài liệu liên quan, hỗ trợ cả API retriever mới và cũ."""
        if hasattr(self.retriever, "invoke"):
            return self.retriever.invoke(question) or []
        if hasattr(self.retriever, "get_relevant_documents"):
            return self.retriever.get_relevant_documents(question) or []
        raise AttributeError("Retriever không hỗ trợ invoke/get_relevant_documents")

    @staticmethod
    def _extract_text_response(result) -> str:
        """Chuẩn hóa phản hồi từ LLM về chuỗi văn bản thuần nhất."""
        if isinstance(result, str):
            return result

        content = getattr(result, "content", None)
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    parts.append(str(part["text"]))
            if parts:
                return "\n".join(parts)

        return str(result)

    @staticmethod
    def _build_citations(documents: list, limit: int = 5) -> list[dict[str, Any]]:
        """Đóng gói metadata cần thiết cho giao diện citation từ danh sách tài liệu."""
        citations = []
        for doc in documents[:limit]:
            metadata = dict(getattr(doc, "metadata", {}) or {})

            citations.append(
                {
                    "source_name": metadata.get("source_name") or metadata.get("source") or "Không rõ nguồn",
                    "page_number": metadata.get("page_number"),
                    "start_index": metadata.get("start_index"),
                    "end_index": metadata.get("end_index"),
                    "chunk_id": metadata.get("chunk_id"),
                    "context": getattr(doc, "page_content", ""),
                }
            )

        return citations

    def ask(self, question: str, return_sources: bool = False):
        """Trả lời câu hỏi và tùy chọn trả về thêm citations nguồn trích dẫn."""
        language = self._detect_language(question)
        documents = self._retrieve_documents(question)
        context = "\n\n".join(
            doc.page_content for doc in documents if getattr(doc, "page_content", "")
        )

        if not context.strip():
            if language == "vi":
                answer = "Tài liệu không có đủ thông tin để trả lời câu hỏi này."
            else:
                answer = "The document does not contain enough information to answer this question."

            if return_sources:
                return {
                    "answer": answer,
                    "citations": [],
                }
            return answer

        template = self._build_template(language)
        prompt = template.format(context=context, question=question)
        result = self.llm.invoke(prompt)
        answer = self._extract_text_response(result)

        if return_sources:
            return {
                "answer": answer,
                "citations": self._build_citations(documents),
            }
        return answer