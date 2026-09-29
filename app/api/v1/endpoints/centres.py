import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.centre import CentreCreate, CentreResponse, TestCreate, TestResponse, CentreTestAssociate
from app.services import centre_service
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
async def create_centre(centre_in: CentreCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await centre_service.create_centre(db, centre_in)

@router.get("/", response_model=List[CentreResponse])
async def list_centres(db: AsyncSession = Depends(get_db)):
    return await centre_service.get_centres(db)

@router.get("/{centre_id}", response_model=CentreResponse)
async def get_centre(centre_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await centre_service.get_centre(db, centre_id)

@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(test_in: TestCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await centre_service.create_test(db, test_in)

@router.get("/tests/", response_model=List[TestResponse])
async def list_tests(db: AsyncSession = Depends(get_db)):
    return await centre_service.get_tests(db)

@router.post("/{centre_id}/tests", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
async def associate_test(centre_id: uuid.UUID, assoc_in: CentreTestAssociate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await centre_service.associate_test_to_centre(db, centre_id, assoc_in)
