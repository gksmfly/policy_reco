import requests

BASE_URL = "http://localhost:8000"

def health():
    return requests.get(f"{BASE_URL}/health").json()

def get_policies():
    return requests.get(f"{BASE_URL}/policies").json()

def recommend(payload):
    return requests.post(f"{BASE_URL}/recommend", json=payload).json()

def policy_qa(payload):
    return requests.post(f"{BASE_URL}/policy-qa", json=payload).json()

def similar(policy_id):
    return requests.get(f"{BASE_URL}/similar/{policy_id}").json()