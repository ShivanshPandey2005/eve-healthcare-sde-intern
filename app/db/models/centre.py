from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base

class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tests = relationship("CentreTestPrice", back_populates="centre")

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    centres = relationship("CentreTestPrice", back_populates="test")

class CentreTestPrice(Base):
    __tablename__ = "centre_test_prices"

    centre_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_centres.id", ondelete="CASCADE"), primary_key=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), primary_key=True)
    price = Column(Numeric(10, 2), nullable=False)

    centre = relationship("DiagnosticCentre", back_populates="tests")
    test = relationship("DiagnosticTest", back_populates="centres")
