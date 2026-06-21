from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analyze_emotion():
    # Write a test that sends text to /api/emotion/analyze
    response = client.post(
        "/api/emotion/analyze",
        json={"text": "烦死了"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # It should not return the fallback "平静" when we say "烦死了"
    assert data["emotion_label"] != "平静"
    
    # Specifically, it should probably return 愤怒, 烦躁, etc.
    # The polarity should definitely not be positive or neutral.
    assert data["polarity"] == "消极"
