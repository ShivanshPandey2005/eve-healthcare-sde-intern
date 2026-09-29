from pydantic import BaseModel
import uuid
from app.db.models.payment import PaymentStatus

class WebhookPayload(BaseModel):
    event_id: str
    payment_id: uuid.UUID
    status: PaymentStatus
