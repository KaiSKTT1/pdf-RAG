"""Fallback helpers khi LLM không phản hồi."""

from __future__ import annotations

from .text_processing import (
    find_section_end,
    looks_like_python_code,
    restore_python_code_layout,
)


def build_brief_retrieval_excerpt(documents: list, max_chars: int = 1200) -> str:
    """Tạo đoạn trích ngắn từ các chunk để fallback khi LLM không sẵn sàng."""
    parts = []
    current_len = 0

    for doc in documents:
        content = str(getattr(doc, "page_content", "") or "").strip()
        if not content:
            continue

        remaining = max_chars - current_len
        if remaining <= 0:
            break

        snippet = content[:remaining]
        parts.append(snippet)
        current_len += len(snippet)

    return "\n\n".join(parts).strip()


def extract_python_code_from_documents(documents: list) -> str:
    """Trích và chuẩn hóa đoạn code Python từ ngữ cảnh retrieval hiện có."""
    joined = "\n\n".join(
        str(getattr(doc, "page_content", "") or "") for doc in documents
    )
    if not joined:
        return ""

    lowered = joined.lower()
    start = lowered.find("def ")
    if start == -1:
        return ""

    end_markers = [
        "c++ implementation",
        "java implementation",
        "\nnguồn trích dẫn:",
        "\nchú thích:",
        "\nsource:",
        "\nsources:",
    ]
    end = find_section_end(lowered, start, end_markers)
    candidate = joined[start:end].strip().strip('"').strip()
    if not looks_like_python_code(candidate):
        return ""

    return restore_python_code_layout(candidate)


def build_quota_fallback_answer(
    question: str,
    documents: list,
    language: str,
    is_code_request_flag: bool,
) -> str:
    """Tạo câu trả lời fallback khi LLM hết quota, chỉ dựa trên context retrieval."""
    _ = question
    python_code = extract_python_code_from_documents(documents) if is_code_request_flag else ""
    excerpt = build_brief_retrieval_excerpt(documents)

    if language == "vi":
        if is_code_request_flag and python_code:
            return (
                "LLM hiện không phản hồi nên hệ thống chuyển sang chế độ fallback từ ngữ cảnh đã truy xuất.\n"
                "Dưới đây là đoạn Python đã được chuẩn hóa thụt lề từ dữ liệu tài liệu:\n\n"
                f"Python Implementation:\n{python_code}\n\n"
                "Lưu ý: Đây là kết quả từ retrieval + OCR, chưa có bước suy luận LLM nâng cao."
            )

        if excerpt:
            return (
                "LLM hiện không phản hồi nên hệ thống chuyển sang chế độ fallback từ ngữ cảnh đã truy xuất.\n"
                "Trích đoạn liên quan từ tài liệu:\n\n"
                f"{excerpt}\n\n"
                "Lưu ý: Đây là kết quả retrieval-only, chưa có bước tổng hợp bằng LLM."
            )

        return "LLM hiện không phản hồi và chưa có ngữ cảnh phù hợp để trả lời."

    if is_code_request_flag and python_code:
        return (
            "The LLM backend is currently unavailable, so the system switched to retrieval-only fallback.\n"
            "Here is the Python snippet normalized from retrieved document context:\n\n"
            f"Python Implementation:\n{python_code}\n\n"
            "Note: This output is retrieval + OCR based without advanced LLM reasoning."
        )

    if excerpt:
        return (
            "The LLM backend is currently unavailable, so the system switched to retrieval-only fallback.\n"
            "Relevant excerpt from retrieved context:\n\n"
            f"{excerpt}\n\n"
            "Note: This is retrieval-only output without LLM synthesis."
        )

    return "The LLM backend is currently unavailable and no relevant retrieved context is available."
