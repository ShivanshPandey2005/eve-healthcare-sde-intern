import pytest
import pytest_asyncio
import uuid
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

@pytest_asyncio.fixture
async def setup_payment(auth_client: AsyncClient, async_client: AsyncClient):
    # Create Centre and Test
    c_res = await auth_client.post("/api/v1/centres/", json={"name": "WH Centre", "location": "Loc"})
    c_id = c_res.json()["id"]

    t_res = await auth_client.post("/api/v1/centres/tests", json={"name": "WH Test", "description": "Desc"})
    t_id = t_res.json()["id"]

    await auth_client.post(f"/api/v1/centres/{c_id}/tests", json={"test_id": t_id, "price": 300.00})
    
    # Create Booking
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    b_res = await auth_client.post(
        "/api/v1/bookings/",
        json={"centre_id": c_id, "test_id": t_id, "appointment_time": future_time}
    )
    booking_id = b_res.json()["id"]

    # Create Payment
    p_res = await auth_client.post("/api/v1/payments/", json={"booking_id": booking_id, "simulate_status": "SUCCESS"})
    payment_id = p_res.json()["id"]

    return {"booking_id": booking_id, "payment_id": payment_id}

@pytest.mark.asyncio
async def test_first_webhook_success(async_client: AsyncClient, auth_client: AsyncClient, setup_payment: dict):
    event_id = str(uuid.uuid4())
    res = await async_client.post(
        "/api/v1/payments/webhook",
        json={"event_id": event_id, "payment_id": setup_payment["payment_id"], "status": "SUCCESS"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "processed"

    b_res = await auth_client.get(f"/api/v1/bookings/{setup_payment['booking_id']}")
    assert b_res.json()["status"] == "CONFIRMED"

@pytest.mark.asyncio
async def test_first_webhook_failed(async_client: AsyncClient, auth_client: AsyncClient, setup_payment: dict):
    event_id = str(uuid.uuid4())
    res = await async_client.post(
        "/api/v1/payments/webhook",
        json={"event_id": event_id, "payment_id": setup_payment["payment_id"], "status": "FAILED"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "processed"

    b_res = await auth_client.get(f"/api/v1/bookings/{setup_payment['booking_id']}")
    assert b_res.json()["status"] == "FAILED"

@pytest.mark.asyncio
async def test_same_webhook_twice(async_client: AsyncClient, setup_payment: dict):
    event_id = str(uuid.uuid4())
    # First request
    res1 = await async_client.post(
        "/api/v1/payments/webhook",
        json={"event_id": event_id, "payment_id": setup_payment["payment_id"], "status": "SUCCESS"}
    )
    assert res1.status_code == 200
    
    # Second request
    res2 = await async_client.post(
        "/api/v1/payments/webhook",
        json={"event_id": event_id, "payment_id": setup_payment["payment_id"], "status": "SUCCESS"}
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "already processed"

@pytest.mark.asyncio
async def test_invalid_payment(async_client: AsyncClient):
    event_id = str(uuid.uuid4())
    res = await async_client.post(
        "/api/v1/payments/webhook",
        json={"event_id": event_id, "payment_id": str(uuid.uuid4()), "status": "SUCCESS"}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Payment not found"

@pytest.mark.asyncio
async def test_concurrent_duplicate_webhooks(async_client: AsyncClient, setup_payment: dict):
    event_id = str(uuid.uuid4())
    
    # Simulate concurrent requests by scheduling them simultaneously
    reqs = [
        async_client.post(
            "/api/v1/payments/webhook",
            json={"event_id": event_id, "payment_id": setup_payment["payment_id"], "status": "SUCCESS"}
        ) for _ in range(5)
    ]
    
    results = await asyncio.gather(*reqs)
    
    processed_count = sum(1 for res in results if res.json().get("status") == "processed")
    already_processed_count = sum(1 for res in results if res.json().get("status") == "already processed")
    
    assert processed_count == 1
    assert already_processed_count == 4
