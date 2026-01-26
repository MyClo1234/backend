import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"


def login(username, password):
    url = f"{BASE_URL}/auth/login"
    response = requests.post(url, json={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()["token"]
    else:
        print(f"Login failed: {response.text}")
        return None


def test_generation(token):
    url = f"{BASE_URL}/generation/outfit"
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "top": {
            "id": "test-top-1",
            "filename": "red_tshirt.jpg",
            "attributes": {
                "category": {"main": "top", "sub": "t-shirt"},
                "color": {"primary": "red", "tone": "bright"},
                "pattern": {"type": "plain"},
                "material": {"guess": "cotton"},
                "fit": {"type": "regular"},
            },
        },
        "bottom": {
            "id": "test-bottom-1",
            "filename": "blue_jeans.jpg",
            "attributes": {
                "category": {"main": "bottom", "sub": "jeans"},
                "color": {"primary": "blue", "tone": "dark"},
                "pattern": {"type": "plain"},
                "material": {"guess": "denim"},
                "fit": {"type": "slim"},
            },
        },
        "style_description": "Casual street style",
        "gender": "female",
    }

    print("Sending generation request (this may take 10-20 seconds)...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("\nSuccess!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nFailed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_generation_manual.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    token = login(username, password)
    if token:
        test_generation(token)
