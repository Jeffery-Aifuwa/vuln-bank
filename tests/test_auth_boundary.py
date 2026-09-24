import requests

def test_unauthenticated_protected_route_denied(base_url):
    """Boundary 1: Accessing protected route without credentials must be denied."""
    response = requests.get(f"{base_url}/dashboard", timeout=5)
    # Token-required endpoints return 401 Unauthorized or redirect
    assert response.status_code in [401, 403, 302]

def test_authenticated_protected_route_accessible(base_url, auth_token):
    """Boundary 2: Accessing protected route with valid Bearer token succeeds."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{base_url}/dashboard", headers=headers, timeout=5)
    assert response.status_code == 200

def test_invalid_token_rejected(base_url):
    """Boundary 3: Accessing protected route with invalid token must be rejected."""
    headers = {"Authorization": "Bearer invalid_forged_token_xyz"}
    response = requests.get(f"{base_url}/dashboard", headers=headers, timeout=5)
    assert response.status_code in [401, 403]

def test_invalid_login_credentials_rejected(base_url):
    """Boundary 4: Attempting to log in with nonexistent credentials must fail."""
    response = requests.post(
        f"{base_url}/login",
        json={"username": "nonexistent_ghost_user", "password": "wrong_password"},
        timeout=5
    )
    assert response.status_code in [400, 401, 404]
