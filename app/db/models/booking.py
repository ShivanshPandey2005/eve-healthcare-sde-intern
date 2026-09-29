import enum
import uuid
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    centre_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_centres.id", ondelete="RESTRICT"), nullable=False)
    test_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_tests.id", ondelete="RESTRICT"), nullable=False)
    appointment_time = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    centre = relationship("DiagnosticCentre")
    test = relationship("DiagnosticTest")
