# EVE Healthcare Backend API

A production-quality backend service for diagnostic test bookings and simulated payments, built for the EVE Healthcare SDE Intern Backend Engineering Assignment.

## 1. Project Overview
EVE Healthcare is a secure backend API that allows users to register, authenticate, and book diagnostic tests across various diagnostic centres. The system manages the entire booking lifecycle from creation through to simulated payment processing via webhooks, all while maintaining rigorous database integrity, idempotency, and strict authorization rules.

## 2. Architecture
The application follows a clean architecture pattern, isolating concerns into specific layers:
- **API Layer (`app/api`):** Handles HTTP requests, Pydantic validation, and response serialization.
- **Service Layer (`app/services`):** Contains core business logic and orchestrates database interactions.
- **Database Layer (`app/db/models`):** SQLAlchemy ORM models representing the database schema.
- **Schemas (`app/schemas`):** Pydantic v2 models for data validation and serialization.
- **Security (`app/core/security.py`):** JWT token generation, validation, and password hashing.

## 3. Tech Stack
- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 (Asyncio)
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Authentication:** JWT (JSON Web Tokens) with bcrypt
- **Testing:** Pytest (with `pytest-asyncio` and `aiosqlite` for in-memory DB testing)
- **Containerization:** Docker & Docker Compose

## 4. Project Structure
```text
eve-healthcare/
├── alembic/                # Database migrations
├── app/
│   ├── api/                # API routes and dependencies
│   ├── core/               # App configuration and security utilities
│   ├── db/                 # Database configuration and SQLAlchemy models
│   ├── schemas/            # Pydantic validation models
│   ├── services/           # Business logic
│   └── main.py             # FastAPI application entry point
├── tests/                  # Comprehensive pytest suite
├── .env.example            # Example environment variables
├── docker-compose.yml      # Infrastructure setup
├── Dockerfile              # Application container build
└── requirements.txt        # Python dependencies
```

## 5. Database Schema
- **`users`**: UUID, Email, Hashed Password.
- **`diagnostic_centres`**: UUID, Name, Location.
- **`diagnostic_tests`**: UUID, Name, Description.
- **`centre_test_prices`**: Association table linking centres and tests with a specific `price`.
- **`bookings`**: UUID, User ID, Centre ID, Test ID, Appointment Time, Amount, Status.
- **`payments`**: UUID, Booking ID, Amount, Status.
- **`webhook_events`**: UUID, Event ID (Unique), Payment ID, Timestamp.

## 6. Authentication Flow
The system uses stateless JWT authentication:
1. User registers via `POST /api/v1/users/signup`. Passwords are securely hashed using bcrypt.
2. User authenticates via `POST /api/v1/users/login` using `OAuth2PasswordRequestForm`.
3. The server validates credentials and issues a JWT access token.
4. Protected routes require the JWT token in the `Authorization: Bearer <token>` header, parsed by the `get_current_user` dependency.

## 7. Booking Lifecycle
Bookings act as a state machine:
- **`PENDING`**: Default state upon creation. Can be cancelled by the user.
- **`CONFIRMED`**: Achieved when a successful payment webhook is processed.
- **`FAILED`**: Occurs if a payment fails.
- **`CANCELLED`**: Initiated by the user prior to payment completion.

## 8. Payment Flow
To maintain isolation between client trust and server truth:
1. Users initiate a mock payment via `POST /api/v1/payments/`.
2. The endpoint verifies the booking exists, belongs to the user, and is `PENDING`.
3. A `Payment` record is created.
4. The endpoint simulates the transaction (either `SUCCESS` or `FAILED`), instantly updating the booking status to match.

## 9. Webhook Idempotency Strategy
The system processes webhooks at `POST /api/v1/payments/webhook`. To handle webhook replays and **concurrent duplicate events**, the application guarantees idempotency through database constraints:
1. A dedicated `WebhookEvent` table tracks processed events using the unique `event_id`.
2. The `event_id` column has a strict `UNIQUE` constraint.
3. When processing a webhook, the application attempts an atomic `INSERT` of the `event_id`.
4. **Concurrency Safety:** If 10 duplicate webhook payloads arrive simultaneously, only the absolute *first* request succeeds. The database natively rejects the others, throwing an `IntegrityError`.
5. The application catches this error, safely rolls back the sub-transaction, and returns a `200 OK` (`"already processed"`) so the payment provider knows to stop retrying.

## 10. API Endpoint Documentation
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/users/signup` | Register a new user | No |
| POST | `/api/v1/users/login` | Obtain a JWT access token | No |
| GET | `/api/v1/users/me` | Fetch authenticated user data | Yes |
| POST | `/api/v1/centres/` | Create a diagnostic centre | Yes |
| GET | `/api/v1/centres/` | List diagnostic centres | No |
| GET | `/api/v1/centres/{id}` | Get a specific centre | No |
| POST | `/api/v1/centres/tests` | Create a diagnostic test | Yes |
| GET | `/api/v1/centres/tests` | List all available tests | No |
| POST | `/api/v1/centres/{id}/tests` | Associate a test with a centre (set price) | Yes |
| POST | `/api/v1/bookings/` | Book a test | Yes |
| GET | `/api/v1/bookings/` | List user's bookings | Yes |
| GET | `/api/v1/bookings/{id}` | Get a specific booking | Yes |
| PATCH | `/api/v1/bookings/{id}/cancel`| Cancel a pending booking | Yes |
| POST | `/api/v1/payments/` | Create a mock payment | Yes |
| POST | `/api/v1/payments/webhook` | Process a payment webhook | No |

## 11. Example Requests/Responses

**Create Booking Request:**
```json
POST /api/v1/bookings/
{
    "centre_id": "c651e4f3-2375-48fd-b5f7-8b427d0577b0",
    "test_id": "3cbb93a0-22a0-4e47-a3e5-9956fe431119",
    "appointment_time": "2026-10-01T10:00:00Z"
}
```

**Create Booking Response:**
```json
{
    "id": "e98e217d-2fb4-4ea0-bd94-32e650ccbbaf",
    "user_id": "4d5f9a91-4d1f-4b09-b4b1-e2e7b9b1b1b1",
    "centre_id": "c651e4f3-2375-48fd-b5f7-8b427d0577b0",
    "test_id": "3cbb93a0-22a0-4e47-a3e5-9956fe431119",
    "appointment_time": "2026-10-01T10:00:00Z",
    "amount": "150.00",
    "status": "PENDING",
    "created_at": "2026-09-29T11:00:00Z",
    "updated_at": "2026-09-29T11:00:00Z"
}
```

## 12. Environment Variables
Copy `.env.example` to `.env`:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eve_healthcare
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 13. Local Setup
1. Clone the repository and initialize a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

## 14. Docker Setup
To run the entire application (App + PostgreSQL) via Docker:
```bash
docker-compose up -d --build
```

## 15. Running Migrations
The database schema is managed via Alembic. To apply migrations:
```bash
alembic upgrade head
```

## 16. Running Tests
The test suite contains **41 integration tests** running against an isolated, in-memory SQLite database (`aiosqlite`) for rapid, side-effect-free execution.
```bash
pytest -v
```

## 17. Swagger Documentation
Once the server is running, the interactive OpenAPI documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## 18. Important Assumptions
- **Price Security:** The client never dictates the price of a booking. The API securely queries the associative `CentreTestPrice` table to determine the amount server-side.
- **Payment Mocking:** The payment endpoint accepts a `simulate_status` payload specifically to aid in triggering explicit success/failure edge cases.
- **Webhook Authentication:** The webhook endpoint (`POST /api/v1/payments/webhook`) is intentionally unauthenticated because it simulates callbacks from an external payment provider. In production, this would be secured with HMAC signature verification or a shared-secret header (e.g., `X-Webhook-Secret`).

## 19. Edge Cases Handled
- Concurrent duplicate webhooks are trapped natively by PostgreSQL to guarantee idempotency.
- Users are strictly authorized so they cannot interact with, view, or modify other users' bookings or payments.
- Duplicate email signups are rejected cleanly via `IntegrityError` rollback handling.
- Booking endpoints enforce future appointment dates only.
- Payment attempts against non-`PENDING` bookings are actively blocked to protect the state machine.

## 20. What Could Be Improved With More Time
- **Webhook HMAC Verification:** Secure the webhook endpoint with cryptographic signature verification.
- **Pagination & Rate Limiting:** Implement cursor or offset-based pagination on list endpoints, and Redis-backed rate limiting to prevent abuse.
- **Roles & Permissions:** Introduce RBAC (e.g., `Admin`, `User`) to restrict the creation of centres/tests strictly to administrators.
- **Robust Observability:** Integrate structured logging (e.g., via `structlog`) and distributed tracing (e.g., OpenTelemetry) to monitor webhook delays.
- **Message Queues:** Offload payment processing and notification dispatching to asynchronous task queues (e.g., Celery/RabbitMQ) for higher resilience.
