import csv
from .base_parser import BaseParser
from core.logger import logger

class CSVParser(BaseParser):
    def parse(self, file_path: str) -> str:
        """
        Parses a CSV file and returns its text content.
        Converts each row into a structured textual representation.
        """
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return ""
                
                rows_text = []
                for row in reader:
                    # Format each row as: Column_Name: Value | Column_Name2: Value2
                    row_parts = []
                    for col, val in row.items():
                        if val:
                            row_parts.append(f"{col}: {val.strip()}")
                    if row_parts:
                        rows_text.append(" | ".join(row_parts))
                
                return "\n".join(rows_text)
        except Exception as e:
            logger.error(f"Failed to parse CSV {file_path}: {e}")
            raise e
