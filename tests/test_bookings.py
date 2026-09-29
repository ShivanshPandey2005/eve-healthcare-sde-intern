import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest_asyncio.fixture
async def setup_centre_test(auth_client: AsyncClient):
    centre_res = await auth_client.post("/api/v1/centres/", json={"name": "Book Centre", "location": "Loc"})
    centre_id = centre_res.json()["id"]

    test_res = await auth_client.post("/api/v1/centres/tests", json={"name": "Book Test", "description": "Desc"})
    test_id = test_res.json()["id"]

    await auth_client.post(f"/api/v1/centres/{centre_id}/tests", json={"test_id": test_id, "price": 100.00})
    return {"centre_id": centre_id, "test_id": test_id}


@pytest.mark.asyncio
async def test_create_booking(auth_client: AsyncClient, setup_centre_test: dict):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": setup_centre_test["test_id"],
            "appointment_time": future_time
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["amount"]) == 100.00
    assert data["status"] == "PENDING"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_booking_past_date(auth_client: AsyncClient, setup_centre_test: dict):
    past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": setup_centre_test["test_id"],
            "appointment_time": past_time
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Appointment time must be in the future"


@pytest.mark.asyncio
async def test_create_booking_nonexistent_centre(auth_client: AsyncClient, setup_centre_test: dict):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": str(uuid.uuid4()),
            "test_id": setup_centre_test["test_id"],
            "appointment_time": future_time
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Test not available at this centre"


@pytest.mark.asyncio
async def test_create_booking_test_not_at_centre(auth_client: AsyncClient, setup_centre_test: dict):
    """Test exists, centre exists, but they are not associated."""
    other_test = await auth_client.post("/api/v1/centres/tests", json={"name": "Unlinked Test"})
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": other_test.json()["id"],
            "appointment_time": future_time
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Test not available at this centre"


@pytest.mark.asyncio
async def test_list_bookings(auth_client: AsyncClient, setup_centre_test: dict):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": setup_centre_test["test_id"],
            "appointment_time": future_time
        }
    )
    response = await auth_client.get("/api/v1/bookings/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_get_booking_not_found(auth_client: AsyncClient):
    response = await auth_client.get(f"/api/v1/bookings/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.asyncio
async def test_cancel_booking(auth_client: AsyncClient, setup_centre_test: dict):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    book_res = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": setup_centre_test["test_id"],
            "appointment_time": future_time
        }
    )
    booking_id = book_res.json()["id"]

    cancel_res = await auth_client.patch(f"/api/v1/bookings/{booking_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_cancel_already_cancelled_booking(auth_client: AsyncClient, setup_centre_test: dict):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    book_res = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": setup_centre_test["test_id"],
            "appointment_time": future_time
        }
    )
    booking_id = book_res.json()["id"]
    await auth_client.patch(f"/api/v1/bookings/{booking_id}/cancel")

    # Try cancelling again
    cancel_res = await auth_client.patch(f"/api/v1/bookings/{booking_id}/cancel")
    assert cancel_res.status_code == 400
    assert "Cannot cancel booking" in cancel_res.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_confirmed_booking(auth_client: AsyncClient, setup_centre_test: dict):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    book_res = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": setup_centre_test["test_id"],
            "appointment_time": future_time
        }
    )
    booking_id = book_res.json()["id"]
    # Pay to confirm
    await auth_client.post("/api/v1/payments/", json={"booking_id": booking_id, "simulate_status": "SUCCESS"})

    cancel_res = await auth_client.patch(f"/api/v1/bookings/{booking_id}/cancel")
    assert cancel_res.status_code == 400
    assert "Cannot cancel booking" in cancel_res.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_booking_access(auth_client: AsyncClient, other_auth_client: AsyncClient, setup_centre_test: dict):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    book_res = await auth_client.post(
        "/api/v1/bookings/",
        json={
            "centre_id": setup_centre_test["centre_id"],
            "test_id": setup_centre_test["test_id"],
            "appointment_time": future_time
        }
    )
    booking_id = book_res.json()["id"]

    get_res = await other_auth_client.get(f"/api/v1/bookings/{booking_id}")
    assert get_res.status_code == 403
    
    cancel_res = await other_auth_client.patch(f"/api/v1/bookings/{booking_id}/cancel")
    assert cancel_res.status_code == 403
