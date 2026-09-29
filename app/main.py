from fastapi import FastAPI
from app.api.v1.endpoints import users, centres, bookings, payments

app = FastAPI(title="EVE Healthcare API", version="1.0.0")

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(centres.router, prefix="/api/v1/centres", tags=["centres"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
