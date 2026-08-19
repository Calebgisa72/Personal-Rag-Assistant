from typing import Type
from .base_parser import BaseParser
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .csv_parser import CSVParser
from .txt_parser import TxtParser

class ParserFactory:
    _parsers = {
        "application/pdf": PDFParser,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
        "text/csv": CSVParser,
        "text/plain": TxtParser,
        "text/html": TxtParser, # Assuming HTML has been pre-processed/scraped into text
    }

    @classmethod
    def get_parser(cls, mime_type: str) -> BaseParser:
        parser_class = cls._parsers.get(mime_type)
        if not parser_class:
            raise ValueError(f"No parser found for MIME type: {mime_type}")
        return parser_class()
