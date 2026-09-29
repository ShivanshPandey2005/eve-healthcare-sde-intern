from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.db.models.payment import PaymentStatus

class PaymentCreate(BaseModel):
    booking_id: uuid.UUID
    # Allow the client to simulate success or failure
    simulate_status: Literal["SUCCESS", "FAILED"] = "SUCCESS"

class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    amount: Decimal
    status: PaymentStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
