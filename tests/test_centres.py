import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_centre(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/centres/",
        json={"name": "City Scan", "location": "Downtown"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "City Scan"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_create_centre_empty_name_rejected(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/centres/",
        json={"name": "", "location": "Downtown"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_test(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/centres/tests",
        json={"name": "Blood Test", "description": "Basic blood panel"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Blood Test"


@pytest.mark.asyncio
async def test_create_duplicate_test_rejected(auth_client: AsyncClient):
    await auth_client.post("/api/v1/centres/tests", json={"name": "Dup Test"})
    response = await auth_client.post("/api/v1/centres/tests", json={"name": "Dup Test"})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_associate_test_to_centre(auth_client: AsyncClient):
    centre_res = await auth_client.post(
        "/api/v1/centres/",
        json={"name": "Health Plus", "location": "Uptown"}
    )
    centre_id = centre_res.json()["id"]

    test_res = await auth_client.post(
        "/api/v1/centres/tests",
        json={"name": "MRI Scan", "description": "Full body MRI"}
    )
    test_id = test_res.json()["id"]

    assoc_res = await auth_client.post(
        f"/api/v1/centres/{centre_id}/tests",
        json={"test_id": test_id, "price": 1500.50}
    )
    
    assert assoc_res.status_code == 201
    data = assoc_res.json()
    assert len(data["tests"]) == 1
    assert data["tests"][0]["test"]["id"] == test_id
    assert float(data["tests"][0]["price"]) == 1500.50


@pytest.mark.asyncio
async def test_associate_test_zero_price_rejected(auth_client: AsyncClient):
    c = await auth_client.post("/api/v1/centres/", json={"name": "ZP Centre", "location": "L"})
    t = await auth_client.post("/api/v1/centres/tests", json={"name": "ZP Test"})
    response = await auth_client.post(
        f"/api/v1/centres/{c.json()['id']}/tests",
        json={"test_id": t.json()["id"], "price": 0}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_associate_test_negative_price_rejected(auth_client: AsyncClient):
    c = await auth_client.post("/api/v1/centres/", json={"name": "NP Centre", "location": "L"})
    t = await auth_client.post("/api/v1/centres/tests", json={"name": "NP Test"})
    response = await auth_client.post(
        f"/api/v1/centres/{c.json()['id']}/tests",
        json={"test_id": t.json()["id"], "price": -50}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_centres(async_client: AsyncClient, auth_client: AsyncClient):
    await auth_client.post("/api/v1/centres/", json={"name": "C1", "location": "L1"})
    response = await async_client.get("/api/v1/centres/")
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_get_centre_not_found(async_client: AsyncClient):
    response = await async_client.get(f"/api/v1/centres/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Centre not found"


@pytest.mark.asyncio
async def test_associate_nonexistent_test(auth_client: AsyncClient):
    c = await auth_client.post("/api/v1/centres/", json={"name": "NT Centre", "location": "L"})
    response = await auth_client.post(
        f"/api/v1/centres/{c.json()['id']}/tests",
        json={"test_id": str(uuid.uuid4()), "price": 100}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Test not found"
