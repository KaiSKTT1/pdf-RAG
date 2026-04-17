"""Điểm vào dạng console để kiểm tra nhanh pipeline RAG trên máy local.

Module này tách biệt với luồng Streamlit, phù hợp cho việc debug
từng bước xử lý mà không phụ thuộc giao diện web.
"""

import os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
os.environ.pop("TRANSFORMERS_CACHE", None)

from loaders.pdf_loader import PDFLoader
from rag.embeddings import Embeddings
from rag.retriever import Retriever
from rag.chain import Chain


class MainApp:
    """Lớp chạy giao diện dòng lệnh cho pipeline RAG phục vụ kiểm thử thủ công."""

    def __init__(self):
        self.pdf_loader = PDFLoader()
        self.embeddings = Embeddings()

    def run(self):
        """Chạy vòng lặp hỏi đáp tương tác trên tài liệu mẫu cố định."""
        file_path = "./data/intro.pdf"

        # Bước 1: tách tài liệu nguồn thành các chunk có ngữ nghĩa.
        chunks = self.pdf_loader.load_and_split(file_path)
        print(f"✓ Tách được {len(chunks)} chunks")

        # Bước 2: sinh embedding cho chunk và lưu vào FAISS.
        vectorstore = self.embeddings.create_vectorstore(chunks)
        print(f"✓ Tạo vectorstore xong! Số vectors: {vectorstore.index.ntotal}")

        # Bước 3: tạo retriever và chain sinh câu trả lời.
        retriever = Retriever(vectorstore)
        chain = Chain(retriever.get_retriever())
        print(f"✓ Chain sẵn sàng!")

        # Bước 4: vòng lặp hỏi đáp tương tác.
        print("\n--- Bắt đầu hỏi đáp (gõ 'exit' để thoát) ---")
        while True:
            question = input("\nCâu hỏi: ")

            if question.lower() == "exit":
                print("Tạm biệt!")
                break

            if question.strip() == "":
                print("Vui lòng nhập câu hỏi!")
                continue

            print("Đang tìm câu trả lời...")
            answer = chain.ask(question)
            print(f"Trả lời: {answer}")

if __name__ == "__main__":
    MainApp().run()