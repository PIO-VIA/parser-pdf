from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from app.main import app
from app.dependencies import get_db
from app.models.user import User

client = TestClient(app)

@pytest.fixture
def mock_db():
    db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()

def test_register_user_success(mock_db):
    # Mock database check (no existing user)
    mock_result_exist = MagicMock()
    mock_result_exist.scalars.return_value.first.return_value = None
    
    # Mock first user check (returning empty list to make them superadmin)
    mock_result_count = MagicMock()
    mock_result_count.scalars.return_value.all.return_value = []
    
    mock_db.execute.side_effect = [mock_result_exist, mock_result_count]

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123",
            "full_name": "Test User"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["code"] == status.HTTP_201_CREATED
    assert data["data"]["user"]["email"] == "test@example.com"
    assert data["data"]["user"]["full_name"] == "Test User"

def test_register_user_already_exists(mock_db):
    # Mock existing user
    mock_user = User(email="test@example.com", hashed_password="hashed")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password",
            "full_name": "Duplicate"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "existe déjà" in data["message"]

@patch("app.services.auth_service.verify_password")
def test_login_success(mock_verify, mock_db):
    mock_verify.return_value = True
    
    # Mock user query
    mock_user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed",
        full_name="Logged User",
        is_active=True,
        is_superadmin=False
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    
    # For registration count check or others if any
    mock_db.execute.return_value = mock_result

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "correctpassword"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "test@example.com"

def test_login_invalid_password(mock_db):
    # Mock user query
    mock_user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_wrong_password",
        is_active=True
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
