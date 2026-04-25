"""Chain hỏi đáp: retrieval + prompt + sinh phản hồi + đóng gói citations."""

from __future__ import annotations

import time

from langchain_ollama import ChatOllama

from config import (
    LLM_NUM_PREDICT,
    LLM_REPEAT_PENALTY,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    MAX_CONTEXT_CHARS,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from .chain_parts.core_utils import (
    build_citations,
    extract_text_response,
    is_quota_error,
    retrieve_documents,
)
from .chain_parts.fallback import build_quota_fallback_answer
from .chain_parts.prompts import build_template, detect_language, is_code_request
from .chain_parts.text_processing import format_context, polish_answer_layout, trim_context


class Chain:
    """Điều phối quy trình truy xuất ngữ cảnh và sinh câu trả lời bằng LLM."""

    def __init__(self, retriever):
        """Khởi tạo LLM local qua Ollama và gắn retriever đã được chuẩn bị trước."""
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=LLM_TEMPERATURE,
            top_p=LLM_TOP_P,
            repeat_penalty=LLM_REPEAT_PENALTY,
            num_predict=LLM_NUM_PREDICT,
        )
        self.retriever = retriever

    def ask(self, question: str, return_sources: bool = False):
        """Trả lời câu hỏi và tùy chọn trả về thêm citations nguồn trích dẫn."""
        t0 = time.perf_counter()
        timings: dict[str, float | int | str] = {}

        language = detect_language(question)
        is_code_request_flag = is_code_request(question)

        t_retrieval_start = time.perf_counter()
        documents = retrieve_documents(self.retriever, question)
        timings["retrieval_seconds"] = time.perf_counter() - t_retrieval_start

        t_context_start = time.perf_counter()
        context = format_context(documents)
        context = trim_context(context, MAX_CONTEXT_CHARS)
        timings["context_seconds"] = time.perf_counter() - t_context_start
        timings["context_chars"] = len(context)

        if not context.strip():
            if language == "vi":
                answer = "Tài liệu không có đủ thông tin để trả lời câu hỏi này."
            else:
                answer = "The document does not contain enough information to answer this question."

            timings["llm_seconds"] = 0.0
            timings["postprocess_seconds"] = 0.0
            timings["total_seconds"] = time.perf_counter() - t0

            if return_sources:
                return {
                    "answer": answer,
                    "citations": [],
                    "timings": timings,
                }
            return answer

        t_prompt_start = time.perf_counter()
        template = build_template(language, is_code_request_flag=is_code_request_flag)
        prompt = template.format(context=context, question=question)
        timings["prompt_seconds"] = time.perf_counter() - t_prompt_start
        timings["prompt_chars"] = len(prompt)

        try:
            t_llm_start = time.perf_counter()
            result = self.llm.invoke(prompt)
            timings["llm_seconds"] = time.perf_counter() - t_llm_start

            t_post_start = time.perf_counter()
            answer = extract_text_response(result)
            if is_code_request_flag:
                answer = polish_answer_layout(answer)
            timings["postprocess_seconds"] = time.perf_counter() - t_post_start
        except Exception as exc:
            timings["llm_seconds"] = timings.get("llm_seconds", 0.0)
            if not is_quota_error(exc):
                raise

            t_fallback_start = time.perf_counter()
            answer = build_quota_fallback_answer(
                question=question,
                documents=documents,
                language=language,
                is_code_request_flag=is_code_request_flag,
            )
            timings["postprocess_seconds"] = time.perf_counter() - t_fallback_start
            timings["fallback"] = "retrieval_only"

        timings["total_seconds"] = time.perf_counter() - t0

        if return_sources:
            return {
                "answer": answer,
                "citations": build_citations(documents),
                "timings": timings,
            }
        return answer
