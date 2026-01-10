""" import requests
import os

def test_analyze_endpoint():
    url = "http://127.0.0.1:8000/analyze"
    test_file = "test_part.step"
    
    if not os.path.exists(test_file):
        print(f"Error: {test_file} not found.")
        return

    with open(test_file, "rb") as f:
        files = {"file": (test_file, f, "application/octet-stream")}
        response = requests.post(url, files=files)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print(response.json())
    else:
        print("Failed!")
        print(response.text)

if __name__ == "__main__":
    test_analyze_endpoint() """
