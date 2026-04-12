from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config import GEMINI_MODEL, GEMINI_API_KEY, LLM_TEMPERATURE

class Chain:
    def __init__(self, retriever):
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=LLM_TEMPERATURE,
            google_api_key=GEMINI_API_KEY
        )
        self.retriever = retriever

    def _detect_language(self, text: str) -> str:
        vietnamese_chars = 'àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ'
        is_vietnamese = any(char in text.lower() for char in vietnamese_chars)
        return "vi" if is_vietnamese else "en"

    def _create_chain(self, language: str) -> RetrievalQA:
        if language == "vi":
            template = """Bạn là trợ lý AI chuyên phân tích tài liệu. Nhiệm vụ của bạn là trả lời câu hỏi DỰA HOÀN TOÀN vào ngữ cảnh được cung cấp.

NGUYÊN TẮC BẮT BUỘC:
- Chỉ sử dụng thông tin có trong ngữ cảnh bên dưới
- Nếu ngữ cảnh không đủ thông tin, hãy nói: "Tài liệu không có đủ thông tin để trả lời câu hỏi này."
- KHÔNG tự bịa thêm thông tin ngoài ngữ cảnh
- Trả lời bằng tiếng Việt, rõ ràng và có cấu trúc

NGỮ CẢNH:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""
        else:
            template = """You are an AI assistant specialized in document analysis. Your task is to answer questions STRICTLY based on the provided context.

MANDATORY RULES:
- Only use information from the context below
- If the context lacks sufficient information, respond: "The document does not contain enough information to answer this question."
- Do NOT fabricate or add information beyond the context
- Be clear, structured, and thorough in your response

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )

        return RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            chain_type_kwargs={"prompt": prompt}
        )

    def ask(self, question: str) -> str:
        language = self._detect_language(question)
        chain = self._create_chain(language)
        result = chain.invoke({"query": question})
        return result["result"]