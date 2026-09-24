import requests

def test_user_registration_and_baseline_balance(base_url, auth_token):
    """Verifies an authenticated user can read their dashboard account state."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    dash = requests.get(f"{base_url}/dashboard", headers=headers, timeout=5)
    assert dash.status_code == 200
    assert "balance" in dash.text.lower() or "account" in dash.text.lower()

def test_transfer_workflow_between_accounts(base_url, auth_token):
    """
    Executes a legitimate fund transfer from the authenticated test user
    to the seeded admin account (ADMIN001).
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    transfer_payload = {
        "to_account": "ADMIN001",
        "amount": 10.00,
        "description": "Baseline automated functional transfer test"
    }
    
    transfer_resp = requests.post(
        f"{base_url}/transfer",
        json=transfer_payload,
        headers=headers,
        timeout=5
    )
    
    assert transfer_resp.status_code == 200
    data = transfer_resp.json()
    assert data.get("status") == "success"
    assert "Transfer Completed" in data.get("message", "")
    assert "new_balance" in data