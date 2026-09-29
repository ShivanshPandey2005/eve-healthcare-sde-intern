from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from decimal import Decimal
import uuid
from datetime import datetime


# Test Schemas
class TestBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class TestCreate(TestBase):
    pass


class TestResponse(TestBase):
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Centre Schemas
class CentreBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)


class CentreCreate(CentreBase):
    pass


# Association Schemas
class CentreTestAssociate(BaseModel):
    test_id: uuid.UUID
    price: Decimal = Field(gt=0, description="Price must be greater than zero")


class CentreTestResponse(BaseModel):
    test: TestResponse
    price: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class CentreResponse(CentreBase):
    id: uuid.UUID
    created_at: datetime
    tests: List[CentreTestResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
