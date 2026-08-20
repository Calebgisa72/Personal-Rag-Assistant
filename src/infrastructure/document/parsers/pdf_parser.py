import fitz  # PyMuPDF
from .base_parser import BaseParser
from core.logger import logger


class PDFParser(BaseParser):
    def parse(self, file_path: str) -> str:
        """
        Parses a PDF file using PyMuPDF and returns its text content.
        Tries to extract text in blocks to preserve some structure (like paragraphs).
        """
        try:
            doc = fitz.open(file_path)
            text_blocks = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # blocks is a list of tuples: (x0, y0, x1, y1, text, block_no, block_type)
                # block_type 0 is text, 1 is image
                blocks = page.get_text("blocks")
                for block in blocks:
                    if block[6] == 0:  # If it is a text block
                        block_text = block[4].strip()
                        if block_text:
                            text_blocks.append(block_text)

            return "\n\n".join(text_blocks)
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise e
