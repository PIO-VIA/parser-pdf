from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, func
import enum
from app.database import Base

class PDFType(str, enum.Enum):
    POLYSOMNOGRAPHIE = "polysomnographie"
    POLYGRAPHIE_PPC = "polygraphie_ppc"
    EFR_STANDARD = "efr_standard"
    EFR_AVANCEE = "efr_avancee"
    UNKNOWN = "unknown"

class PDFStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class PDFFile(Base):
    __tablename__ = "pdf_files"
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    temp_path = Column(String, nullable=True)   # null after deletion
    pdf_type = Column(Enum(PDFType), default=PDFType.UNKNOWN, nullable=False)
    status = Column(Enum(PDFStatus), default=PDFStatus.PENDING, nullable=False)
    error_message = Column(String, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    parsed_at = Column(DateTime, nullable=True)
