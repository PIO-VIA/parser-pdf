from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.pdf_file import PDFType, PDFStatus

class PDFFileBase(BaseModel):
    original_filename: str
    pdf_type: PDFType
    status: PDFStatus
    error_message: Optional[str] = None

class PDFFileOut(PDFFileBase):
    id: int
    uploaded_by: Optional[int] = None
    created_at: datetime
    parsed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PDFUploadResponse(BaseModel):
    pdf_file_id: int
    status: PDFStatus
