"""Xử lý text cho Chain: sanitize context và polish câu trả lời."""

from __future__ import annotations

import re


def sanitize_context_text(text: str) -> str:
    """Làm sạch nhẹ context để giảm lỗi dính dòng nhưng không làm mất dữ liệu."""
    normalized = (text or "").replace("\r\n", "\n")
    normalized = re.sub(
        r"\s*(Python Implementation|C\+\+\s*Implementation|Java Implementation)\s*",
        r"\n\1\n",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\s+(?=def\s+[A-Za-z_][A-Za-z0-9_]*\s*\()",
        "\n",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\s+(?=public\s+static\s+void\s+[A-Za-z_][A-Za-z0-9_]*\s*\()",
        "\n",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\s+(?=void\s+[A-Za-z_][A-Za-z0-9_]*\s*\()",
        "\n",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def find_section_end(lower_text: str, start_index: int, markers: list[str]) -> int:
    """Tìm vị trí kết thúc gần nhất của một section dựa trên danh sách marker."""
    indices = []
    for marker in markers:
        idx = lower_text.find(marker, start_index + 1)
        if idx != -1:
            indices.append(idx)
    return min(indices) if indices else len(lower_text)


def extract_python_segment(text: str) -> tuple[int, int, str] | None:
    """Trích đúng đoạn Python code trong câu trả lời, tránh nuốt cả block ngôn ngữ khác."""
    lowered = text.lower()
    start = lowered.find("def ")
    if start == -1:
        return None

    end_markers = [
        "c++ implementation",
        "java implementation",
        "\nnguồn trích dẫn:",
        "\nchú thích:",
        "\nsource:",
        "\nsources:",
    ]
    end = find_section_end(lowered, start, end_markers)

    segment = text[start:end].strip().strip('"').strip()
    segment = re.sub(r"['\"]\s*['\"]\s*$", "", segment).strip()
    segment = re.sub(r"['\"]\s*$", "", segment).strip()
    if not segment:
        return None
    return start, end, segment


def looks_like_python_code(text: str) -> bool:
    """Nhận diện nhanh đoạn text có khả năng là mã Python."""
    lowered = (text or "").lower()
    signals = ["def ", "for ", "if ", "return", "while ", "class ", "arr[", ":"]
    score = sum(1 for signal in signals if signal in lowered)
    return score >= 3 and ":" in lowered


def restore_python_code_layout(text: str) -> str:
    """Chuẩn hóa đoạn code Python OCR bị dính dòng về dạng dễ đọc."""
    if not text:
        return ""

    candidate = re.sub(r"\s+", " ", text).strip()
    candidate = re.sub(r"\bfor\s+1\s+in\b", "for i in", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bj\+l\b", "j+1", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bj\+I\b", "j+1", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+sort\b", r"\1_sort", candidate)

    candidate = re.sub(
        r"\s+(?=(?:def|for|if|elif|else|while|return|class|try|except|finally)\b)",
        "\n",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r":\s+(?=(?:for|if|elif|else|while|return)\b)",
        ":\n",
        candidate,
        flags=re.IGNORECASE,
    )

    raw_lines = [line.strip() for line in candidate.splitlines() if line.strip()]
    if not raw_lines:
        return text

    expanded_lines: list[str] = []
    inline_block_pattern = re.compile(
        r"^(def|for|if|elif|else|while|class|try|except|finally)\b(.*?):\s+(.+)$",
        flags=re.IGNORECASE,
    )
    for line in raw_lines:
        match = inline_block_pattern.match(line)
        if match:
            expanded_lines.append(f"{match.group(1)}{match.group(2)}:")
            expanded_lines.append(match.group(3).strip())
        else:
            expanded_lines.append(line)

    formatted_lines: list[str] = []
    indent_level = 0

    for line in expanded_lines:
        line_lower = line.lower()
        if line_lower.startswith(("elif", "else", "except", "finally")):
            indent_level = max(indent_level - 1, 0)

        if line_lower.startswith("return ") and indent_level > 1:
            indent_level = 1

        line = re.sub(r"\s+([,:;\)\]\}])", r"\1", line)
        line = re.sub(r"([\(\[\{])\s+", r"\1", line)
        line = re.sub(r",(?=\S)", ", ", line)
        line = re.sub(r"\s{2,}", " ", line).strip()

        formatted_lines.append(f"{'    ' * indent_level}{line}")

        if line.endswith(":"):
            indent_level += 1

    return "\n".join(formatted_lines).strip()


def polish_answer_layout(answer: str) -> str:
    """Làm đẹp câu trả lời: ưu tiên sửa đoạn code Python OCR bị dính dòng."""
    if not answer:
        return ""

    normalized_answer = answer.replace("\r\n", "\n")
    segment_info = extract_python_segment(normalized_answer)
    if not segment_info:
        return re.sub(r"\n{3,}", "\n\n", normalized_answer).strip()

    start, end, candidate_code = segment_info
    if not looks_like_python_code(candidate_code):
        return re.sub(r"\n{3,}", "\n\n", normalized_answer).strip()

    if candidate_code.count("\n") >= 4 and re.search(r"^\s{4,}\S", candidate_code, flags=re.MULTILINE):
        return re.sub(r"\n{3,}", "\n\n", normalized_answer).strip()

    formatted_code = restore_python_code_layout(candidate_code)
    formatted_code = re.sub(r"['\"]\s*$", "", formatted_code).strip()
    if not formatted_code:
        return re.sub(r"\n{3,}", "\n\n", normalized_answer).strip()

    prefix = normalized_answer[:start].rstrip()
    suffix = normalized_answer[end:].lstrip().lstrip('"').lstrip()

    prefix = re.sub(
        r"(Python Implementation|Triển khai Python|Cài đặt Python)\s*[:\-]?\s*$",
        "",
        prefix,
        flags=re.IGNORECASE,
    ).rstrip().rstrip('"').rstrip()

    rebuilt_parts = []
    if prefix:
        rebuilt_parts.append(prefix)
    rebuilt_parts.append(f"Python Implementation:\n{formatted_code}")
    if suffix:
        rebuilt_parts.append(suffix)

    polished = "\n\n".join(part for part in rebuilt_parts if part)
    polished = re.sub(
        r"\"\s*(C\+\+\s*Implementation|Java Implementation)",
        r"\n\1",
        polished,
        flags=re.IGNORECASE,
    )
    polished = re.sub(
        r"\"\s*(Nguồn trích dẫn:|Chú thích:|Source:|Sources:)",
        r"\n\1",
        polished,
        flags=re.IGNORECASE,
    )
    polished = re.sub(r"\n\s*\"\s*\n", "\n", polished)
    polished = re.sub(r"\"\s*$", "", polished)
    polished = re.sub(r"\n{3,}", "\n\n", polished)
    return polished.strip()


def format_context(documents: list) -> str:
    """Định dạng context theo từng chunk để mô hình đọc rõ nguồn và giảm lẫn nội dung."""
    blocks = []
    for idx, doc in enumerate(documents, start=1):
        content = sanitize_context_text(getattr(doc, "page_content", ""))
        if not content:
            continue

        metadata = dict(getattr(doc, "metadata", {}) or {})
        source_name = metadata.get("source_name") or metadata.get("source") or "Không rõ nguồn"
        page_number = metadata.get("page_number")
        chunk_id = metadata.get("chunk_id")

        header_parts = [f"Chunk {idx}", f"source={source_name}"]
        if page_number is not None:
            header_parts.append(f"page={page_number}")
        if chunk_id is not None:
            header_parts.append(f"chunk_id={chunk_id}")

        header = " | ".join(header_parts)
        blocks.append(f"[{header}]\n{content}")

    return "\n\n-----\n\n".join(blocks)


def trim_context(context: str, max_chars: int) -> str:
    """Giới hạn độ dài context để giữ thời gian suy luận ổn định."""
    if max_chars <= 0:
        return context

    if len(context) <= max_chars:
        return context

    divider = "\n\n-----\n\n"
    cut_index = context.rfind(divider, 0, max_chars)
    if cut_index != -1 and cut_index >= int(max_chars * 0.6):
        return context[:cut_index].rstrip()

    return context[:max_chars].rstrip()
