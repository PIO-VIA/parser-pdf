import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add project path to python path
sys.path.append("/home/pio/Documents/FAST_API/medical_backend")

from app.services.pdf_detector import detect_pdf_type
from app.services.parsers.efr_avancee_parser import EFRAvanceeParser
from app.services.parsers.efr_standard_parser import EFRStandardParser
from app.services.parsers.polygraphie_ppc_parser import PolygraphiePPCParser
from app.services.parsers.polysomnographie_parser import PolysomnographieParser
from app.models.pdf_file import PDFType

async def check_pdf(filepath):
    print(f"\n--- Testing: {filepath} ---")
    pdf_type = detect_pdf_type(filepath)
    print(f"Detected Type: {pdf_type}")
    
    # Instantiate appropriate parser
    parser = None
    if pdf_type == PDFType.EFR_AVANCEE:
        parser = EFRAvanceeParser(filepath, pdf_file_id=1)
    elif pdf_type == PDFType.EFR_STANDARD:
        parser = EFRStandardParser(filepath, pdf_file_id=1)
    elif pdf_type == PDFType.POLYGRAPHIE_PPC:
        parser = PolygraphiePPCParser(filepath, pdf_file_id=1)
    elif pdf_type == PDFType.POLYSOMNOGRAPHIE:
        parser = PolysomnographieParser(filepath, pdf_file_id=1)
    else:
        print("Unknown PDF Type")
        return

    # Extract all text using parser's base method to inspect patient line
    text = parser.extract_all_text()
    print("Sample lines from text:")
    for line in text.split("\n")[:30]:
        if any(keyword in line.lower() for keyword in ["nom", "prénom", "sexe", "age", "né le", "naissance"]):
            print(f"  [PATIENT LINE]: {line}")
            
    # Mock AsyncSession to avoid DB write
    class DummySession:
        def add(self, record):
            self.record = record
        async def flush(self):
            pass

    dummy_db = DummySession()
    record = await parser.parse(dummy_db)
    
    # Print parsed patient info
    res = {}
    for attr in ["patient_nom", "patient_prenom", "patient_dob", "genre", "patient_age", "taille", "poids"]:
        if hasattr(record, attr):
            res[attr] = getattr(record, attr)
    print(f"Parsed Patient Info: {res}")

async def main():
    pdfs = [
        "HURIAU_SANDRINE_Polygraphie_2025-05-13.pdf",
        "HANOUN_DJAMEL_EFR_2026-05-30.pdf",
        "LADRIERE_DOROTHEE_Polysomnographie_2026-05-27.pdf"
    ]
    for pdf in pdfs:
        if os.path.exists(pdf):
            await check_pdf(pdf)
        else:
            print(f"File not found: {pdf}")

if __name__ == "__main__":
    asyncio.run(main())
