import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse
from app.services import booking_service
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking_in: BookingCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await booking_service.create_booking(db, booking_in, current_user)

@router.get("/", response_model=List[BookingResponse])
async def list_bookings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await booking_service.get_user_bookings(db, current_user)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await booking_service.get_booking(db, booking_id, current_user)

@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await booking_service.cancel_booking(db, booking_id, current_user)
