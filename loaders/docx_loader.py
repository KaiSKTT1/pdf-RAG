from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE
from loaders.base_loader import BaseLoader


class DOCXLoader(BaseLoader):
    def load_and_split(self, file_path: str) -> list:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        if not documents:
            return []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        return splitter.split_documents(documents)
