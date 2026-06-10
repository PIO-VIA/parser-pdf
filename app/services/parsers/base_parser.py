from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

class BaseParser(ABC):
    def __init__(self, filepath: str, pdf_file_id: int):
        self.filepath = filepath
        self.pdf_file_id = pdf_file_id

    def extract_all_text(self) -> str:
        text = ""
        with pdfplumber.open(self.filepath) as pdf:
            text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
        
        if len(text.strip()) < 50:
            try:
                images = convert_from_path(self.filepath)
                ocr_text = "\n".join(
                    pytesseract.image_to_string(img, lang='fra') for img in images
                )
                return ocr_text
            except Exception:
                pass
                
        return text

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
