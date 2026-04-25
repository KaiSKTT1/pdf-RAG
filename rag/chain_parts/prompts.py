"""Prompt helpers cho Chain hỏi đáp."""

from __future__ import annotations


def detect_language(text: str) -> str:
    """Phát hiện nhanh ngôn ngữ câu hỏi để chọn prompt vi/en phù hợp."""
    vietnamese_chars = "àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
    is_vietnamese = any(char in text.lower() for char in vietnamese_chars)
    return "vi" if is_vietnamese else "en"


def is_code_request(question: str) -> bool:
    """Nhận diện câu hỏi đang yêu cầu mã nguồn hoặc định dạng code."""
    lowered = (question or "").lower()
    keywords = [
        "code",
        "mã",
        "python",
        "c++",
        "java",
        "hàm",
        "function",
        "thụt",
        "indent",
        "syntax",
    ]
    return any(keyword in lowered for keyword in keywords)


def build_template(language: str, is_code_request_flag: bool = False) -> str:
    """Trả về prompt ngắn gọn theo ngôn ngữ đầu vào để tối ưu tốc độ phản hồi."""
    if language == "vi":
        if is_code_request_flag:
            return """Bạn là trợ lý AI phân tích tài liệu.

YÊU CẦU:
- Chỉ dùng thông tin trong ngữ cảnh.
- Nếu thiếu dữ liệu, trả đúng câu: Tài liệu không có đủ thông tin để trả lời câu hỏi này.
- Trả lời ngắn gọn, tối đa 12 dòng.
- Nếu câu hỏi yêu cầu code: chỉ xuất code có trong ngữ cảnh; không thêm logic mới.
- Nếu code Python bị dính dòng, chuẩn hóa thụt lề 4 spaces để dễ chạy.

NGỮ CẢNH:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""

        return """Bạn là trợ lý AI phân tích tài liệu.

YÊU CẦU:
- Chỉ dùng thông tin trong ngữ cảnh.
- Nếu thiếu dữ liệu, trả đúng câu: Tài liệu không có đủ thông tin để trả lời câu hỏi này.
- Trả lời trực diện, rõ ý, tối đa 6 câu.

NGỮ CẢNH:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""

    if is_code_request_flag:
        return """You are an AI assistant for document QA.

RULES:
- Use only the provided context.
- If context is insufficient, reply exactly: The document does not contain enough information to answer this question.
- Keep output concise, maximum 12 lines.
- For code requests, return only code grounded in context and keep original logic.
- If Python code is flattened, normalize to 4-space indentation.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    return """You are an AI assistant for document QA.

RULES:
- Use only the provided context.
- If context is insufficient, reply exactly: The document does not contain enough information to answer this question.
- Keep output direct and concise, maximum 6 sentences.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
