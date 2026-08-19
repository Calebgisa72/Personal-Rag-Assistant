from .base_parser import BaseParser
from core.logger import logger

class TxtParser(BaseParser):
    def parse(self, file_path: str) -> str:
        """
        Parses a basic text file and returns its text content.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to parse TXT {file_path}: {e}")
            raise e
