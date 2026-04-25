"""Tiện ích dùng chung cho main area: kiểm tra tài liệu, lỗi, chuẩn hóa câu trả lời."""

import re


def is_supported_document(uploaded_file) -> bool:
    """Kiểm tra file upload có thuộc định dạng PDF/DOCX được hỗ trợ hay không."""
    file_name = (uploaded_file.name or "").lower()
    mime_type = (uploaded_file.type or "").lower()
    if file_name.endswith(".pdf") or mime_type == "application/pdf":
        return True

    if (
        file_name.endswith(".docx")
        or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return True

    return False


def friendly_model_error(exc: Exception) -> str:
    """Chuyển exception kỹ thuật thành thông báo thân thiện cho người dùng."""
    error_text = str(exc)
    error_lower = error_text.lower()

    if "resourceexhausted" in error_lower or "quota" in error_lower or "429" in error_lower:
        return "Backend LLM báo vượt hạn mức/tốc độ. Vui lòng thử lại sau hoặc đổi backend."
    if (
        "api key" in error_lower
        or "permission denied" in error_lower
        or "unauthorized" in error_lower
    ):
        return "Thông tin xác thực backend không hợp lệ hoặc chưa được cấp quyền."
    if "ollama" in error_lower or "connection refused" in error_lower or "localhost:11434" in error_lower:
        return "Không kết nối được Ollama. Hãy chạy 'ollama serve' và kiểm tra model qwen2.5 đã pull." 
    if "connect" in error_lower or "connection" in error_lower or "timeout" in error_lower:
        return "Không kết nối được tới dịch vụ mô hình. Vui lòng kiểm tra Ollama rồi thử lại."

    return f"Lỗi khi gọi mô hình: {error_text}"


def normalize_answer_text(text: str) -> str:
    """Chuẩn hóa câu trả lời markdown về văn bản thuần dễ đọc trên giao diện."""
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n")

    # Loại bỏ ký hiệu heading markdown.
    normalized = re.sub(r"^\s*#{1,6}\s*", "", normalized, flags=re.MULTILINE)

    # Chuyển bullet markdown thành bullet dễ đọc.
    normalized = re.sub(r"^\s*[*+-]\s+", "• ", normalized, flags=re.MULTILINE)

    # Bỏ ký hiệu in đậm thường bị rò vào bản hiển thị văn bản thuần.
    normalized = normalized.replace("**", "")

    # Bỏ cặp dấu code fence nếu mô hình trả về nhầm.
    normalized = normalized.replace("```", "")

    # Sửa trường hợp tiêu đề mục bị dính liền như "1.Giải thuật1.1 Bubble sort".
    normalized = re.sub(r"(?<!\d)(\d+\.)(?=[A-Za-zÀ-ỹ])", r"\1 ", normalized)
    normalized = re.sub(r"(?<!\d)(\d+\.\d+)(?=[A-Za-zÀ-ỹ])", r"\1 ", normalized)
    normalized = re.sub(
        r"(?<=[A-Za-zÀ-ỹ\)])(?=(?:\d+\.\d+|\d+\.)\s*[A-Za-zÀ-ỹ(])",
        "\n",
        normalized,
    )
    normalized = re.sub(
        r"(?<=[:;])\s*(?=(?:\d+\.\d+|\d+\.)\s*[A-Za-zÀ-ỹ(])",
        "\n",
        normalized,
    )

    # Thêm xuống dòng theo cấu trúc khi mô hình trả về đoạn văn bị nén.
    normalized = re.sub(
        r"(?<=\S)\s+(?=Chương\s+\d+\s*:)",
        "\n",
        normalized,
    )
    normalized = re.sub(
        r"(?<=\S)\s+(?=(?:\d+\.\d+)\s+[A-Za-zÀ-ỹ(])",
        "\n",
        normalized,
    )
    normalized = re.sub(
        r"(?<=\S)\s+(?=•\s)",
        "\n",
        normalized,
    )

    # Giữ khoảng trắng gọn gàng nhưng vẫn bảo toàn ngắt dòng chủ đích.
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()