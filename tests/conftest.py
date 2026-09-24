import os
import time
import uuid
import pytest
import requests

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:5000").rstrip("/")

@pytest.fixture(scope="session")
def base_url():
    return TARGET_URL

@pytest.fixture
def unique_credentials():
    uid = uuid.uuid4().hex[:8]
    return {
        "username": f"user_{uid}_{int(time.time())}",
        "password": "ValidPassword123!"
    }

@pytest.fixture
def registered_user(base_url, unique_credentials):
    """Registers a fresh test user and returns their credentials and account info."""
    resp = requests.post(
        f"{base_url}/register",
        json=unique_credentials,
        timeout=5
    )
    assert resp.status_code in [200, 201], f"Registration failed: {resp.text}"
    return unique_credentials

@pytest.fixture
def auth_token(base_url, registered_user):
    """Logs in the registered user and returns the JWT token string."""
    resp = requests.post(
        f"{base_url}/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        },
        timeout=5
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    token = data.get("token")
    assert token, f"Token not present in login response: {data}"
    return token
