from langchain_community.vectorstores import FAISS
from config import SEARCH_TYPE, TOP_K, FETCH_K

# User đưa prompt thì Retriever sẽ tìm kiếm trong vectorstore FAISS
class Retriever:
    def __init__(self, vectorstore: FAISS):
        self.retriever = vectorstore.as_retriever(
            search_type=SEARCH_TYPE,
            search_kwargs={
                "k": TOP_K,
                "fetch_k": FETCH_K
            }
        )

    def get_retriever(self):
        return self.retriever