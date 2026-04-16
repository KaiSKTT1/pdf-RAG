from abc import ABC, abstractmethod

class BaseLoader(ABC):
    @abstractmethod
    def load_and_split(self, file_path: str, chunk_size: int, chunk_overlap: int) -> list:
        pass