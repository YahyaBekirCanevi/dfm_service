from fastapi.testclient import TestClient
from app.main import app
import os
import json

client = TestClient(app)

def test_file(file_path):
    print(f"\nTesting file: {file_path}")
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return
        
    with open(file_path, "rb") as f:
        response = client.post("/analyze", files={"file": f})
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"BBox: {data['bounding_box']}")
        print(f"Features: {data['features']}")
        print("DFM Feedback:")
        for fb in data['dfm_feedback']:
            print(f" - [{fb['severity']}] {fb['rule_id']}: {fb['message']}")
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_dir = "test_data"
    # Wait for test files to be created if running in parallel
    import time
    time.sleep(1) 
    
    files = [
        "violation.step",
        "violation.stl",
        "success.step",
        "success.stl"
    ]
    
    for f in files:
        test_file(os.path.join(test_dir, f))
