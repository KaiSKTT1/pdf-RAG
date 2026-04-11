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
            template = """Sử dụng ngữ cảnh sau đây để trả lời câu hỏi.
Nếu bạn không biết, chỉ cần nói là bạn không biết.
Trả lời ngắn gọn (3-4 câu) BẮT BUỘC bằng tiếng Việt.

Ngữ cảnh: {context}

Câu hỏi: {question}

Trả lời:"""
        else:
            template = """Use the following context to answer the question.
If you don't know the answer, just say you don't know.
Keep answer concise (3-4 sentences).

Context: {context}

Question: {question}

Answer:"""

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