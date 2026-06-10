import io
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from app.main import app
from app.dependencies import get_db, get_current_user
from app.models.user import User

client = TestClient(app)

@pytest.fixture
def mock_auth_and_db():
    mock_user = User(id=1, email="test@example.com", is_active=True, is_superadmin=True)
    db = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db
    yield mock_user, db
    app.dependency_overrides.clear()

def test_upload_invalid_file_type(mock_auth_and_db):
    # Send a non-PDF file content-type
    files = {"file": ("test.txt", b"some plain text content", "text/plain")}
    response = client.post("/api/v1/pdf/upload", files=files)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "PDF" in data["message"]

def test_upload_invalid_magic_bytes(mock_auth_and_db):
    # Send application/pdf content-type but invalid starting bytes
    files = {"file": ("test.pdf", b"not a real pdf content", "application/pdf")}
    response = client.post("/api/v1/pdf/upload", files=files)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "PDF" in data["message"]

@patch("app.routers.pdf.process_pdf")
def test_upload_success(mock_process, mock_auth_and_db):
    user, db = mock_auth_and_db
    # Mock database insert
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    # Valid PDF magic bytes prefix %PDF-
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj"
    files = {"file": ("report.pdf", pdf_content, "application/pdf")}
    
    response = client.post("/api/v1/pdf/upload", files=files)
    
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["message"] == "PDF reçu, traitement en cours"
    assert "pdf_file_id" in data["data"]
