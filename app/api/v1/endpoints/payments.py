import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.schemas.webhook import WebhookPayload
from app.services import payment_service
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payment_in: PaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await payment_service.process_payment(db, payment_in, current_user)

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    return await payment_service.process_webhook(db, payload)
