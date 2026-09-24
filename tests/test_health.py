import requests

def test_root_endpoint_returns_200(base_url):
    response = requests.get(f"{base_url}/", timeout=5)
    assert response.status_code == 200
    assert "VulnBank" in response.text or len(response.text) > 0

def test_healthz_endpoint(base_url):
    response = requests.get(f"{base_url}/healthz", timeout=5)
    assert response.status_code == 200
