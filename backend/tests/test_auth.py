import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_lifecycle(client: AsyncClient):
    """
    Tests the complete user auth lifecycle: register, login, refresh, logout.
    """
    user_email = "test_user@example.com"
    user_password = "ComplexPassword123!"

    # 1. Register User
    register_payload = {
        "email": user_email,
        "password": user_password
    }
    register_resp = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    reg_body = register_resp.json()
    assert reg_body["status"] == "success"
    assert reg_body["data"]["email"] == user_email
    assert reg_body["data"]["role"] == "admin"  # First registered user defaults to admin

    # 2. Register Duplicate User (should fail)
    dup_resp = await client.post("/api/v1/auth/register", json=register_payload)
    assert dup_resp.status_code == 400
    dup_body = dup_resp.json()
    assert dup_body["status"] == "error"
    assert "already exists" in dup_body["message"]

    # 3. Login
    login_payload = {
        "email": user_email,
        "password": user_password
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_body = login_resp.json()
    assert login_body["status"] == "success"
    assert "access_token" in login_body["data"]
    
    # Assert HTTP-Only cookie was set
    assert "refresh_token" in login_resp.cookies
    refresh_cookie = login_resp.cookies["refresh_token"]
    assert refresh_cookie is not None

    access_token = login_body["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 4. Refresh Token Verification
    # Note: client automatically carries cookies from previous requests
    import asyncio
    await asyncio.sleep(1)  # Ensure token timestamp changes
    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    refresh_body = refresh_resp.json()
    assert refresh_body["status"] == "success"
    assert "access_token" in refresh_body["data"]
    new_access_token = refresh_body["data"]["access_token"]
    assert new_access_token != access_token

    # 5. Logout User
    logout_headers = {"Authorization": f"Bearer {new_access_token}"}
    logout_resp = await client.post("/api/v1/auth/logout", headers=logout_headers)
    assert logout_resp.status_code == 200
    logout_body = logout_resp.json()
    assert logout_body["status"] == "success"

    # 6. Verify Old Session / Cookie is invalid after logout
    failed_refresh_resp = await client.post("/api/v1/auth/refresh")
    assert failed_refresh_resp.status_code == 401
