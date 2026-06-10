from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
import pdfplumber

class BaseParser(ABC):
    def __init__(self, filepath: str, pdf_file_id: int):
        self.filepath = filepath
        self.pdf_file_id = pdf_file_id

    def extract_all_text(self) -> str:
        with pdfplumber.open(self.filepath) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )

    def extract_tables(self) -> list:
        tables = []
        with pdfplumber.open(self.filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_tables()
                if t:
                    tables.extend(t)
        return tables

    @abstractmethod
    async def parse(self, db: AsyncSession) -> dict:
        """Parse the PDF, persists to DB, and returns the created record dict or object."""
        pass
