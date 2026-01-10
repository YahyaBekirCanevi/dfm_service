from fastapi.testclient import TestClient
from app.main import app
import os
import json

client = TestClient(app)

def test_v2_part(file_path):
    print(f"\nTesting V2 file: {file_path}")
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return
        
    with open(file_path, "rb") as f:
        response = client.post("/analyze", files={"file": f})
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print("Features Extracted:")
        print(json.dumps(data['features'], indent=2))
        print("DFM Feedback:")
        for fb in data['dfm_feedback']:
            print(f" - [{fb['severity']}] {fb['rule_id']}: {fb['message']}")
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_dir = "test_data_v2"
    test_v2_part(os.path.join(test_dir, "complex_part.step"))
