import os
import requests
from fastapi.testclient import TestClient
from backend import app

client = TestClient(app)

def test_api():
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    data = health_resp.json()
    assert data["status"] == "online"

    story_payload = {
        "prompt": "A brave young rabbit discovering a hidden magical garden.",
        "target_age": "5-8 years"
    }
    story_resp = client.post("/api/generate-story", json=story_payload)
    assert story_resp.status_code == 200
    story_data = story_resp.json()
    assert len(story_data["pages"]) == 5
    assert story_data["character"]["name"]

    img_dir = os.path.join("generated", "test_run")
    sample_images = [
        os.path.join(img_dir, f"page_{i}.jpg") for i in range(1, 6)
    ]
    
    pdf_payload = {
        "storybook": story_data,
        "image_paths": sample_images
    }
    pdf_resp = client.post("/api/generate-pdf", json=pdf_payload)
    assert pdf_resp.status_code == 200
    pdf_info = pdf_resp.json()
    assert "download_url" in pdf_info
    
    filename = pdf_info["filename"]
    dl_resp = client.get(f"/api/download-pdf/{filename}")
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert len(dl_resp.content) > 1000

    print("ALL FASTAPI BACKEND TESTS PASSED!")

if __name__ == "__main__":
    test_api()
