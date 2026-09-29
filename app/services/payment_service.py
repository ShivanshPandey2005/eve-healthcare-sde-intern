from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from fastapi import HTTPException, status
import uuid

from app.db.models.user import User
from app.db.models.booking import Booking, BookingStatus
from app.db.models.payment import Payment, PaymentStatus
from app.db.models.webhook import WebhookEvent
from app.schemas.payment import PaymentCreate
from app.schemas.webhook import WebhookPayload
from app.services.booking_service import get_booking


async def process_payment(db: AsyncSession, payment_in: PaymentCreate, current_user: User) -> Payment:
    # 1, 2, 3: Fetch booking and ensure it belongs to the user
    booking = await get_booking(db, payment_in.booking_id, current_user)

    # 4: Ensure payment is allowed for this booking state
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Payment not allowed for booking in {booking.status.value} state"
        )

    # 5: Create mock payment record
    mock_status = PaymentStatus.SUCCESS if payment_in.simulate_status == "SUCCESS" else PaymentStatus.FAILED
    
    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=mock_status
    )
    
    db.add(payment)
    
    # 6, 7: Update booking status accordingly
    if mock_status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED
        
    db.add(booking)
    
    # Commit transaction atomically
    await db.commit()
    await db.refresh(payment)
    
    return payment


async def process_webhook(db: AsyncSession, payload: WebhookPayload):
    """
    Idempotent webhook processing strategy:
    
    1. Insert the WebhookEvent row (with unique event_id) and flush (not commit).
    2. Fetch and update Payment + Booking state.
    3. Commit everything in a single atomic transaction.
    
    If a duplicate event_id arrives, the flush raises IntegrityError immediately.
    We rollback and return 200 OK ("already processed") — no state is corrupted.
    
    This eliminates the crash window that would exist if we committed the event_id
    insert separately from the state update.
    """
    webhook_event = WebhookEvent(event_id=payload.event_id, payment_id=payload.payment_id)
    db.add(webhook_event)
    
    try:
        # Flush sends the INSERT to the DB and triggers the unique constraint check,
        # but does NOT commit. The row is visible within this transaction only.
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return {"status": "already processed"}

    # Fetch payment and booking within the SAME transaction
    result = await db.execute(select(Payment).where(Payment.id == payload.payment_id))
    payment = result.scalar_one_or_none()
    
    if not payment:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        
    result = await db.execute(select(Booking).where(Booking.id == payment.booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Update states based on payload status
    payment.status = payload.status
    if payload.status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    elif payload.status == PaymentStatus.FAILED:
        booking.status = BookingStatus.FAILED
        
    db.add(payment)
    db.add(booking)
    
    # Single atomic commit: WebhookEvent insert + Payment/Booking state update
    await db.commit()
    
    return {"status": "processed"}
