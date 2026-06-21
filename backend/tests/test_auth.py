import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

def test_login_and_history():
    # 1. Register a user
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]

    # 2. Login with correct credentials
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200
    login_data = response.json()
    assert "access_token" in login_data
    assert login_data["access_token"] == token or login_data["access_token"] != ""
    
    # 3. Login with incorrect credentials (this should return 400 Bad Request as expected by frontend, it's not a bug but checking behavior)
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 400

    # 4. Fetch history using Authorization header
    response = client.get("/api/auth/history", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200  # Currently this fails with 422
