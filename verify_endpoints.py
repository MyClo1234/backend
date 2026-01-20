import requests
import time
import sys

BASE_URL = "http://localhost:8000/api"

def test_health():
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print("Health check PASSED")
            return True
        else:
            print(f"Health check FAILED: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Health check ERROR: {e}")
        return False

def test_wardrobe_items():
    try:
        resp = requests.get(f"{BASE_URL}/wardrobe/items")
        if resp.status_code == 200:
            print("Wardrobe items check PASSED")
            return True
        else:
            print(f"Wardrobe items check FAILED: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Wardrobe items check ERROR: {e}")
        return False

def main():
    print("Waiting for server to start...")
    time.sleep(5)
    
    if not test_health():
        sys.exit(1)
        
    if not test_wardrobe_items():
        sys.exit(1)
        
    print("All basic checks passed.")

if __name__ == "__main__":
    main()
