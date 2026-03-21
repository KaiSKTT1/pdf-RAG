import os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
os.environ.pop("TRANSFORMERS_CACHE", None)

from config import EMBEDDING_MODEL, EMBEDDING_DEVICE, EMBEDDING_NORMALIZE
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

class Embeddings:

    # Khởi tạo embedder để tạo vector embedding cho văn bản
    def __init__(self):
        self.embedder = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": EMBEDDING_NORMALIZE},
        )

    def create_vectorstore(self, chunks: list) -> FAISS:
        # Tạo vectorstore từ các chunks đã được chia nhỏ và embedder vào vectorDB FAISS
        # 1. embed tất cả chunks → vector
        # 2. lưu vào FAISS index luôn
        self.vectorstore = FAISS.from_documents(chunks, self.embedder)
        return self.vectorstore

    def get_vectorstore(self) -> FAISS:
        return self.vectorstore
