import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest_asyncio.fixture
async def setup_booking(auth_client: AsyncClient):
    c_res = await auth_client.post("/api/v1/centres/", json={"name": "P Centre", "location": "Loc"})
    c_id = c_res.json()["id"]

    t_res = await auth_client.post("/api/v1/centres/tests", json={"name": "P Test", "description": "Desc"})
    t_id = t_res.json()["id"]

    await auth_client.post(f"/api/v1/centres/{c_id}/tests", json={"test_id": t_id, "price": 200.00})
    
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    b_res = await auth_client.post(
        "/api/v1/bookings/",
        json={"centre_id": c_id, "test_id": t_id, "appointment_time": future_time}
    )
    return b_res.json()["id"]


@pytest.mark.asyncio
async def test_successful_payment(auth_client: AsyncClient, setup_booking: str):
    pay_res = await auth_client.post(
        "/api/v1/payments/",
        json={"booking_id": setup_booking, "simulate_status": "SUCCESS"}
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["status"] == "SUCCESS"
    
    b_res = await auth_client.get(f"/api/v1/bookings/{setup_booking}")
    assert b_res.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_failed_payment(auth_client: AsyncClient, setup_booking: str):
    pay_res = await auth_client.post(
        "/api/v1/payments/",
        json={"booking_id": setup_booking, "simulate_status": "FAILED"}
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["status"] == "FAILED"
    
    b_res = await auth_client.get(f"/api/v1/bookings/{setup_booking}")
    assert b_res.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_invalid_booking(auth_client: AsyncClient):
    pay_res = await auth_client.post(
        "/api/v1/payments/",
        json={"booking_id": str(uuid.uuid4()), "simulate_status": "SUCCESS"}
    )
    assert pay_res.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_payment(other_auth_client: AsyncClient, setup_booking: str):
    pay_res = await other_auth_client.post(
        "/api/v1/payments/",
        json={"booking_id": setup_booking, "simulate_status": "SUCCESS"}
    )
    assert pay_res.status_code == 403


@pytest.mark.asyncio
async def test_duplicate_payment_attempt_on_confirmed(auth_client: AsyncClient, setup_booking: str):
    await auth_client.post("/api/v1/payments/", json={"booking_id": setup_booking, "simulate_status": "SUCCESS"})
    
    pay_res = await auth_client.post("/api/v1/payments/", json={"booking_id": setup_booking, "simulate_status": "SUCCESS"})
    assert pay_res.status_code == 400
    assert "Payment not allowed" in pay_res.json()["detail"]


@pytest.mark.asyncio
async def test_pay_cancelled_booking(auth_client: AsyncClient, setup_booking: str):
    await auth_client.patch(f"/api/v1/bookings/{setup_booking}/cancel")
    
    pay_res = await auth_client.post("/api/v1/payments/", json={"booking_id": setup_booking, "simulate_status": "SUCCESS"})
    assert pay_res.status_code == 400
    assert "Payment not allowed" in pay_res.json()["detail"]
