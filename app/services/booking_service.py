import uuid
from typing import List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.db.models.user import User
from app.db.models.booking import Booking, BookingStatus
from app.db.models.centre import CentreTestPrice
from app.schemas.booking import BookingCreate

async def create_booking(db: AsyncSession, booking_in: BookingCreate, current_user: User) -> Booking:
    # Normalize naive datetime to UTC
    appointment = booking_in.appointment_time
    if appointment.tzinfo is None:
        appointment = appointment.replace(tzinfo=timezone.utc)
    if appointment < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment time must be in the future")

    # Verify that the centre offers the test and fetch the price
    result = await db.execute(
        select(CentreTestPrice)
        .where(CentreTestPrice.centre_id == booking_in.centre_id)
        .where(CentreTestPrice.test_id == booking_in.test_id)
    )
    association = result.scalar_one_or_none()
    
    if not association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not available at this centre")

    booking = Booking(
        user_id=current_user.id,
        centre_id=booking_in.centre_id,
        test_id=booking_in.test_id,
        appointment_time=booking_in.appointment_time,
        amount=association.price, # Server-side price
        status=BookingStatus.PENDING
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking

async def get_user_bookings(db: AsyncSession, current_user: User) -> List[Booking]:
    result = await db.execute(select(Booking).where(Booking.user_id == current_user.id))
    return result.scalars().all()

async def get_booking(db: AsyncSession, booking_id: uuid.UUID, current_user: User) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this booking")
        
    return booking

async def cancel_booking(db: AsyncSession, booking_id: uuid.UUID, current_user: User) -> Booking:
    booking = await get_booking(db, booking_id, current_user)
    
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot cancel booking in {booking.status.value} state")
        
    booking.status = BookingStatus.CANCELLED
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
