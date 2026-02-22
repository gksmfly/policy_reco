import requests

BASE_URL = "http://localhost:8000"


def health():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_policies():
    try:
        r = requests.get(f"{BASE_URL}/policies", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def recommend(payload):
    try:
        r = requests.post(f"{BASE_URL}/recommend", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def policy_qa(payload):
    try:
        r = requests.post(f"{BASE_URL}/policy-qa", json=payload, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def similar(policy_id):
    try:
        r = requests.get(f"{BASE_URL}/similar/{policy_id}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}