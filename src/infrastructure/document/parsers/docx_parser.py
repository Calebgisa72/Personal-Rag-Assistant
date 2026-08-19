import docx
from .base_parser import BaseParser
from core.logger import logger

class DocxParser(BaseParser):
    def parse(self, file_path: str) -> str:
        """
        Parses a DOCX file and returns its text content.
        Preserves paragraph boundaries.
        """
        try:
            doc = docx.Document(file_path)
            paragraphs = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)
                    
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            raise e
