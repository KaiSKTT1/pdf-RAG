"""Tiện ích lõi cho luồng hỏi đáp RAG."""

from __future__ import annotations

from typing import Any


def retrieve_documents(retriever, question: str) -> list:
    """Lấy tài liệu liên quan, hỗ trợ cả API retriever mới và cũ."""
    if hasattr(retriever, "invoke"):
        return retriever.invoke(question) or []
    if hasattr(retriever, "get_relevant_documents"):
        return retriever.get_relevant_documents(question) or []
    raise AttributeError("Retriever không hỗ trợ invoke/get_relevant_documents")


def extract_text_response(result) -> str:
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


def is_quota_error(exc: Exception) -> bool:
    """Nhận diện lỗi tạm thời (quota/timeout/kết nối) để chuyển sang fallback."""
    error_text = str(exc).lower()
    quota_signals = [
        "resourceexhausted",
        "quota",
        "429",
        "rate limit",
        "too many requests",
        "timeout",
        "timed out",
        "read timeout",
        "connection refused",
        "failed to connect",
        "temporarily unavailable",
    ]
    return any(signal in error_text for signal in quota_signals)


def build_citations(documents: list, limit: int = 5) -> list[dict[str, Any]]:
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
