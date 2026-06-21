import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)

@patch("services.matcher.redis_client", new_callable=AsyncMock)
def test_match(mock_redis):
    # Setup mock behavior
    mock_redis.set.return_value = None
    mock_redis.rpush.return_value = None
    mock_redis.get.return_value = None
    mock_redis.lrange.return_value = []
    
    response = client.post("/api/ws/match", json={
        "user_id": "user123",
        "emotion_label": "快乐",
        "intensity": 8,
        "polarity": "积极",
        "keywords": ["开心", "哈哈"]
    })
    
    print(response.status_code)
    print(response.text)
    assert response.status_code == 200
