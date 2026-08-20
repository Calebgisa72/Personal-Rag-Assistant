from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        Parses the file at the given path and returns its text content.
        For advanced formats, this can return structured markdown.
        """
        pass
