from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

import re
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
                    pytesseract.image_to_string(img, lang='fra', config='--psm 6') for img in images
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
                    
        # If no tables are found, build simulated tables from OCR text lines
        if not tables:
            text = self.extract_all_text()
            simulated_rows = []
            
            # Helper to check if a split token is a pure numeric value or standard placeholder
            def is_pure_value(tok):
                tok_clean = tok.replace("%", "").strip()
                if not tok_clean:
                    return False
                # Check if it matches a standard float/int pattern
                if re.match(r"^[-+]?\d*(?:[.,]\d+)?$", tok_clean):
                    if tok_clean in (".", ",", "+", "-"):
                        return False
                    return True
                # Check if it matches standard empty placeholders
                if re.match(r"^[-—_~–]+$", tok_clean):
                    return True
                return False

            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                # Find the index of the first pure value token
                val_start_idx = -1
                for idx, tok in enumerate(parts):
                    if is_pure_value(tok):
                        val_start_idx = idx
                        break
                
                if val_start_idx != -1:
                    label = " ".join(parts[:val_start_idx])
                    values = parts[val_start_idx:]
                else:
                    label = " ".join(parts)
                    values = []
                
                # Ensure the label is present and not just numeric/placeholder
                if label and len(label) >= 2:
                    row = [label] + values
                    simulated_rows.append(row)
            
            if simulated_rows:
                tables = [simulated_rows]
                
        return tables

    @abstractmethod
    async def parse(self, db: AsyncSession) -> dict:
        """Parse the PDF, persists to DB, and returns the created record dict or object."""
        pass
