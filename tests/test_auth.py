import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_successful_signup(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/users/signup",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_duplicate_email(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/users/signup",
        json={"email": "dup@example.com", "password": "securepassword"}
    )
    response = await async_client.post(
        "/api/v1/users/signup",
        json={"email": "dup@example.com", "password": "securepassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_invalid_email_format(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/users/signup",
        json={"email": "not-an-email", "password": "securepassword"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_short_password_rejected(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/users/signup",
        json={"email": "short@example.com", "password": "abc"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_successful_login(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/users/signup",
        json={"email": "login@example.com", "password": "securepassword"}
    )
    response = await async_client.post(
        "/api/v1/users/login",
        data={"username": "login@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_invalid_password(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/users/signup",
        json={"email": "wrong@example.com", "password": "securepassword"}
    )
    response = await async_client.post(
        "/api/v1/users/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/users/login",
        data={"username": "nobody@example.com", "password": "password123"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(async_client: AsyncClient):
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(async_client: AsyncClient):
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer garbage.token.here"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/users/signup",
        json={"email": "token@example.com", "password": "securepassword"}
    )
    login_response = await async_client.post(
        "/api/v1/users/login",
        data={"username": "token@example.com", "password": "securepassword"}
    )
    token = login_response.json()["access_token"]
    
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "token@example.com"
