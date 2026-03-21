from abc import ABC, abstractmethod

class BaseLoader(ABC):
    @abstractmethod
    def load_and_split(self,file_path:str) -> list:
        pass