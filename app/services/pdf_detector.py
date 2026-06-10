import pdfplumber
from app.models.pdf_file import PDFType

def detect_pdf_type(filepath: str) -> PDFType:
    with pdfplumber.open(filepath) as pdf:
        text = ""
        # Analyze up to the first 2 pages
        for page in pdf.pages[:2]:
            t = page.extract_text()
            if t:
                text += t.lower()

    # Detection rules based on characteristic keywords
    if "rapport de polysomnographie" in text or "polysomnographie" in text:
        return PDFType.POLYSOMNOGRAPHIE

    if "polygraphie sous ppc" in text or "rapport de polygraphie" in text:
        return PDFType.POLYGRAPHIE_PPC

    # EFR avancée: contains plethysmography + diffusion keywords
    if ("plethysmograph" in text or "pléthysmograph" in text) and (
        "dlco" in text or "diffusion" in text
    ):
        return PDFType.EFR_AVANCEE

    # EFR standard: spirometry + plethysmography without diffusion
    if "spirometri" in text or "vems" in text or "cvf" in text or "efr" in text:
        return PDFType.EFR_STANDARD

    return PDFType.UNKNOWN
