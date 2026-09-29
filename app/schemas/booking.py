from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from decimal import Decimal
from app.db.models.booking import BookingStatus

class BookingCreate(BaseModel):
    centre_id: uuid.UUID
    test_id: uuid.UUID
    appointment_time: datetime

class BookingResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    centre_id: uuid.UUID
    test_id: uuid.UUID
    appointment_time: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
