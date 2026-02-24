import pytest
import os
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_step_content():
    # Simple valid-looking STEP content (minimal header)
    return b"ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''),'2;1');\nFILE_NAME('','',(),(),'','','');\nFILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"

def test_analyze_invalid_extension():
    response = client.post(
        "/analyze",
        files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]

def test_analyze_missing_file():
    # FastAPI handles this automatically if 'file' is required
    response = client.post("/analyze")
    assert response.status_code == 422

# These tests might fail if OCCT is not configured to handle dummy content 
# but they test the API wrapping logic.
# In a real environment, we'd use small valid STEP files.

@pytest.mark.skip(reason="Requires valid binary STEP/STL files to pass OCCT loading")
def test_analyze_step_endpoint(sample_step_content):
    response = client.post(
        "/analyze",
        files={"file": ("test.step", io.BytesIO(sample_step_content), "application/octet-stream")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "geometry_index" in data
    assert "dfm_feedback" in data

def test_api_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200
