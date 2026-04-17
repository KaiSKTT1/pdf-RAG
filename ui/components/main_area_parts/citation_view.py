import html
import re
from difflib import SequenceMatcher

import streamlit as st

from .utils import normalize_answer_text


"""Tiện ích UI cho citation.

Module này chịu trách nhiệm:
- Tìm đoạn trong câu trả lời tương ứng với từng nguồn citation.
- Hiển thị highlight có thể bấm.
- Hiển thị badge nguồn + chú thích + cửa sổ nổi context.
"""


_STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "have", "for", "are", "was",
    "các", "những", "được", "trong", "của", "và", "cho", "với", "khi", "trên",
    "một", "này", "đó", "là", "về", "không", "cần", "nên", "đang", "câu",
}


def extract_highlight_terms(question: str, answer: str, max_terms: int = 12) -> list[str]:
    """Trích từ khóa nổi bật từ question + answer để tô context gốc."""
    text = f"{question} {answer}".lower()
    tokens = re.findall(r"[a-zA-Z0-9À-ỹ]{3,}", text)

    unique_terms = []
    for token in tokens:
        if token.isdigit() or token in _STOPWORDS:
            continue
        if token not in unique_terms:
            unique_terms.append(token)
        if len(unique_terms) >= max_terms:
            break

    return sorted(unique_terms, key=len, reverse=True)


def highlight_context(context: str, terms: list[str]) -> str:
    """Bọc các từ xuất hiện trong context bằng thẻ <mark> và trả HTML an toàn."""
    if not context:
        return ""

    if not terms:
        return html.escape(context).replace("\n", "<br>")

    pattern = re.compile("|".join(re.escape(term) for term in terms), re.IGNORECASE)
    parts = []
    cursor = 0

    for match in pattern.finditer(context):
        parts.append(html.escape(context[cursor:match.start()]))
        parts.append(f"<mark>{html.escape(match.group(0))}</mark>")
        cursor = match.end()

    parts.append(html.escape(context[cursor:]))
    return "".join(parts).replace("\n", "<br>")


def _normalize_range(text: str, start: int, end: int) -> tuple[int, int]:
    """Kẹp biên start/end vào phạm vi hợp lệ và loại khoảng trắng ở rìa."""
    text_len = len(text)
    start = max(0, min(start, text_len))
    end = max(start, min(end, text_len))

    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1

    return start, end


def _expand_range_to_clause(
    text: str,
    start: int,
    end: int,
    min_chars: int = 32,
) -> tuple[int, int]:
    """Mở rộng match ngắn thành cụm/câu gần nhất để highlight dễ đọc hơn."""
    text_len = len(text)
    if text_len == 0:
        return 0, 0

    left_window_start = max(0, start - 180)
    left_chunk = text[left_window_start:start]
    left_rel = max(left_chunk.rfind(ch) for ch in ".!?\n")
    if left_rel != -1:
        left = left_window_start + left_rel + 1
    else:
        left = max(0, start - 70)

    right_window_end = min(text_len, end + 180)
    right_chunk = text[end:right_window_end]
    right_match = re.search(r"[.!?\n]", right_chunk)
    if right_match:
        right = end + right_match.start() + 1
    else:
        right = min(text_len, end + 70)

    if right - left < min_chars:
        extra = ((min_chars - (right - left)) // 2) + 1
        left = max(0, left - extra)
        right = min(text_len, right + extra)

    return _normalize_range(text, left, right)


def _resolve_citation_ranges(answer: str, citations: list[dict]) -> list[dict]:
    """Tìm đoạn answer tương ứng cho từng citation và tránh chồng lấn đoạn."""
    answer_lower = answer.lower()
    selected_ranges: list[dict] = []

    for citation_idx, citation in enumerate(citations, start=1):
        context = (citation.get("context") or "").strip()
        if not context:
            continue

        match = SequenceMatcher(None, answer_lower, context.lower()).find_longest_match(
            0,
            len(answer_lower),
            0,
            len(context),
        )
        if match.size >= 18:
            start = match.a
            end = match.a + match.size
        else:
            start = -1
            end = -1

            candidate_tokens = []
            for token in re.findall(r"[a-zA-Z0-9À-ỹ]{5,}", context.lower()):
                if token in _STOPWORDS:
                    continue
                if token in candidate_tokens:
                    continue
                candidate_tokens.append(token)

            candidate_tokens.sort(key=len, reverse=True)
            for token in candidate_tokens:
                token_pos = answer_lower.find(token)
                if token_pos != -1:
                    start = token_pos
                    end = token_pos + len(token)
                    break
            if start == -1:
                continue

        start, end = _normalize_range(answer, start, end)
        if end - start < 24:
            start, end = _expand_range_to_clause(answer, start, end, min_chars=34)

        start, end = _normalize_range(answer, start, end)
        if end - start < 12:
            continue

        overlaps_existing = any(
            not (end <= item["start"] or start >= item["end"])
            for item in selected_ranges
        )
        if overlaps_existing:
            continue

        selected_ranges.append(
            {
                "start": start,
                "end": end,
                "citation_idx": citation_idx,
            }
        )

    return sorted(selected_ranges, key=lambda x: x["start"])


def _source_class(citation_idx: int) -> str:
    """Ánh xạ chỉ số nguồn sang lớp CSS màu sắc nhất quán."""
    palette_idx = ((citation_idx - 1) % 4) + 1
    return f"citation-source-{palette_idx}"


def _safe_ref_token(raw: str) -> str:
    """Chuẩn hóa chuỗi làm id anchor để tránh ký tự HTML không hợp lệ."""
    token = re.sub(r"[^a-zA-Z0-9_-]", "-", raw or "")
    return token or "msg"


def _overlay_id(message_ref: str, citation_idx: int) -> str:
    """Sinh id anchor cho cửa sổ nổi của từng citation."""
    return f"citation-overlay-{_safe_ref_token(message_ref)}-{citation_idx}"


def _reset_id(message_ref: str) -> str:
    """Sinh id anchor dùng để đóng cửa sổ nổi và quay về trạng thái bình thường."""
    return f"citation-reset-{_safe_ref_token(message_ref)}"


def _trim_text(text: str, max_len: int = 22) -> str:
    """Rút gọn văn bản để hiển thị gọn trong chip/chú thích."""
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def _legend_snippet_for_citation(
    citation_idx: int,
    citation: dict,
    answer: str,
    ranges: list[dict],
) -> str:
    """Lấy đoạn đại diện cho chú thích: ưu tiên đoạn đã khớp, dự phòng sang context."""
    for item in ranges:
        if item.get("citation_idx") == citation_idx:
            snippet = answer[item["start"]:item["end"]].strip()
            if snippet:
                return _trim_text(snippet)

    context = str(citation.get("context") or "").strip()
    if context:
        context_tokens = re.findall(r"[a-zA-Z0-9À-ỹ]{3,}", context)
        if context_tokens:
            return _trim_text(" ".join(context_tokens[:3]))
    return f"Nguồn {citation_idx}"


def _citation_location_text(citation: dict) -> str:
    """Định dạng chuỗi vị trí nguồn (trang/start-end) để hiển thị trên giao diện."""
    page_number = citation.get("page_number")
    start_index = citation.get("start_index")
    end_index = citation.get("end_index")

    location_parts = []
    if isinstance(page_number, int):
        location_parts.append(f"trang {page_number}")
    if isinstance(start_index, int) and isinstance(end_index, int):
        location_parts.append(f"vị trí {start_index}-{end_index}")
    if not location_parts:
        return "không có metadata vị trí"
    return ", ".join(location_parts)


def _citation_hover_text(index: int, citation: dict) -> str:
    """Chuỗi tooltip cho highlight và badge nguồn."""
    source_name = str(citation.get("source_name") or "Không rõ nguồn")
    location = _citation_location_text(citation)
    return f"Nguồn {index} - {source_name} ({location})"


def _render_answer_with_clickable_highlights(
    answer: str,
    citations: list[dict],
    message_ref: str,
) -> tuple[str, list[dict]]:
    """Chuyển câu trả lời thành HTML có highlight bấm được và trả kèm vùng đã ánh xạ."""
    ranges = _resolve_citation_ranges(answer, citations)
    if not ranges:
        return html.escape(answer).replace("\n", "<br>"), []

    parts: list[str] = []
    cursor = 0

    for item in ranges:
        start, end, citation_idx = item["start"], item["end"], item["citation_idx"]
        parts.append(html.escape(answer[cursor:start]).replace("\n", "<br>"))

        css_class = _source_class(citation_idx)
        overlay_id = _overlay_id(message_ref, citation_idx)
        hover_text = html.escape(_citation_hover_text(citation_idx, citations[citation_idx - 1]), quote=True)
        parts.append(
            f"<a class='citation-highlight {css_class}' href='#{overlay_id}' title='{hover_text}'>"
            f"{html.escape(answer[start:end])}</a>"
        )
        cursor = end

    parts.append(html.escape(answer[cursor:]).replace("\n", "<br>"))

    return "".join(parts), ranges


def _citation_badge_label(index: int, citation: dict) -> str:
    """Nhãn badge nguồn: ưu tiên số trang, dự phòng theo index nguồn."""
    page_number = citation.get("page_number")
    if isinstance(page_number, int):
        return f"Trang {page_number}"
    return f"Nguồn {index}"


def _render_citation_meta(
    citations: list[dict],
    message_ref: str,
    answer: str,
    ranges: list[dict],
) -> str:
    """Tạo HTML cho hàng badge nguồn và hàng chú thích."""
    if not citations:
        return ""

    badge_html = []
    for idx, citation in enumerate(citations, start=1):
        css_class = _source_class(idx)
        overlay_id = _overlay_id(message_ref, idx)
        hover_text = html.escape(_citation_hover_text(idx, citation), quote=True)
        badge_html.append(
            f"<a class='citation-badge {css_class}' href='#{overlay_id}' title='{hover_text}'>"
            f"{html.escape(_citation_badge_label(idx, citation))}</a>"
        )

    legend_items = []
    for idx, citation in enumerate(citations, start=1):
        css_class = _source_class(idx)
        snippet = _legend_snippet_for_citation(idx, citation, answer, ranges)
        legend_items.append(
            f"<span class='citation-legend-chip {css_class}'>{html.escape(snippet)}</span> "
            f"<span class='citation-legend-label'>Nguồn {idx}</span>"
        )

    return (
        "<div class='citation-meta-row'>"
        "<span class='citation-meta-title'>Nguồn trích dẫn:</span>"
        f"{''.join(badge_html)}"
        "</div>"
        "<div class='citation-legend-row'>"
        "<span class='citation-meta-title'>Chú thích:</span>"
        f"{' '.join(legend_items)}"
        "</div>"
    )

def _build_overlay_markup(
    citations: list[dict],
    message_ref: str,
    question: str,
    answer: str,
) -> str:
    """Tạo HTML cửa sổ nổi cho từng citation để xem context gốc khi bấm."""
    if not citations:
        return ""

    reset_id = _reset_id(message_ref)
    overlays = [f"<div id='{reset_id}' class='citation-overlay-reset-anchor'></div>"]
    highlight_terms = extract_highlight_terms(question, answer)

    for idx, citation in enumerate(citations, start=1):
        source_name = str(citation.get("source_name") or "Không rõ nguồn")
        location_text = _citation_location_text(citation)
        context_html = highlight_context(str(citation.get("context") or ""), highlight_terms)
        if not context_html:
            context_html = "Không có context để hiển thị."

        overlay_id = _overlay_id(message_ref, idx)
        overlays.append(
            "<div "
            f"id='{overlay_id}' "
            "class='citation-overlay-target'>"
            f"<a class='citation-overlay-backdrop' href='#{reset_id}' aria-label='Đóng'></a>"
            "<div class='citation-modal' role='dialog' aria-modal='true'>"
            f"<a class='citation-modal-close' href='#{reset_id}' aria-label='Đóng'>×</a>"
            f"<div class='citation-modal-title'>Nguồn {idx}: {html.escape(source_name)}</div>"
            f"<div class='citation-modal-subtitle'>Vị trí: {html.escape(location_text)}</div>"
            "<div class='citation-modal-label'>Context gốc</div>"
            f"<div class='citation-context-box'>{context_html}</div>"
            "</div>"
            "</div>"
        )

    return "".join(overlays)


def render_citations(
    citations: list[dict],
    question: str,
    answer: str,
    message_ref: str,
    ranges: list[dict],
) -> None:
    """Hiển thị khối citation (đường ngăn + metadata + cửa sổ nổi) dưới câu trả lời."""
    if not citations:
        return

    citation_meta_html = _render_citation_meta(citations, message_ref, answer, ranges)
    overlay_html = _build_overlay_markup(citations, message_ref, question, answer)

    st.markdown(
        "<div class='citation-divider'></div>"
        f"{citation_meta_html}"
        f"{overlay_html}",
        unsafe_allow_html=True,
    )


def render_assistant_message(message: dict, message_ref: str | None = None) -> None:
    """Hàm vào chính để hiển thị phản hồi assistant kèm đầy đủ giao diện citation."""
    answer = normalize_answer_text(message.get("content", ""))
    question = message.get("question", "")
    citations = message.get("citations", [])

    resolved_message_ref = message_ref or f"msg_{abs(hash(answer)) % 100000}"
    answer_html, ranges = _render_answer_with_clickable_highlights(
        answer,
        citations,
        resolved_message_ref,
    )
    st.markdown(f"<div class='citation-answer'>{answer_html}</div>", unsafe_allow_html=True)
    render_citations(citations, question, answer, resolved_message_ref, ranges)