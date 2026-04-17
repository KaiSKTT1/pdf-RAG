"""Tầng embedding: chuyển văn bản thành vector và quản lý FAISS vectorstore."""

import os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
os.environ.pop("TRANSFORMERS_CACHE", None)

from config import EMBEDDING_MODEL, EMBEDDING_DEVICE, EMBEDDING_NORMALIZE
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class Embeddings:
    """Bao gói model embedding và thao tác tạo/lấy vectorstore."""

    def __init__(self):
        """Khởi tạo embedding model theo cấu hình trong config.py."""
        self.embedder = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": EMBEDDING_NORMALIZE},
        )

    def create_vectorstore(self, chunks: list) -> FAISS:
        """Sinh embedding cho chunks và tạo FAISS index từ kết quả đó."""
        self.vectorstore = FAISS.from_documents(chunks, self.embedder)
        return self.vectorstore

    def get_vectorstore(self) -> FAISS:
        """Trả về vectorstore hiện tại đã được tạo trước đó."""
        return self.vectorstore
