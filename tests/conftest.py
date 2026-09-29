import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.database import Base, get_db
from app.main import app

# Use an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

import pytest_asyncio

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def auth_client(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/users/signup",
        json={"email": "admin@example.com", "password": "securepassword"}
    )
    login_response = await async_client.post(
        "/api/v1/users/login",
        data={"username": "admin@example.com", "password": "securepassword"}
    )
    token = login_response.json()["access_token"]
    async_client.headers.update({"Authorization": f"Bearer {token}"})
    return async_client

@pytest_asyncio.fixture
async def other_auth_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/users/signup", json={"email": "other@example.com", "password": "otherpassword"})
        res = await client.post("/api/v1/users/login", data={"username": "other@example.com", "password": "otherpassword"})
        client.headers.update({"Authorization": f"Bearer {res.json()['access_token']}"})
        yield client
