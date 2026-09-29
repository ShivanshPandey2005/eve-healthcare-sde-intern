import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base

class WebhookEvent(Base):
    """
    Idempotency strategy:
    To ensure idempotent webhook processing and handle concurrent duplicates, 
    we store every processed webhook's unique event_id here with a UNIQUE constraint.
    When processing a webhook, we attempt to insert this record as part of the transaction.
    If an IntegrityError is raised due to a duplicate event_id, we know it's a replay or
    a concurrent duplicate, and we can safely catch it, rollback, and return a 200 OK 
    (to acknowledge receipt without corrupting state).
    """
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
