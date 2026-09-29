import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.models.centre import DiagnosticCentre, DiagnosticTest, CentreTestPrice
from app.schemas.centre import CentreCreate, TestCreate, CentreTestAssociate

async def create_centre(db: AsyncSession, centre_in: CentreCreate) -> DiagnosticCentre:
    centre = DiagnosticCentre(**centre_in.model_dump())
    db.add(centre)
    await db.commit()
    return await get_centre(db, centre.id)

async def get_centres(db: AsyncSession) -> list[DiagnosticCentre]:
    result = await db.execute(select(DiagnosticCentre).options(selectinload(DiagnosticCentre.tests).selectinload(CentreTestPrice.test)))
    return result.scalars().all()

async def get_centre(db: AsyncSession, centre_id: uuid.UUID) -> DiagnosticCentre:
    result = await db.execute(
        select(DiagnosticCentre)
        .options(selectinload(DiagnosticCentre.tests).selectinload(CentreTestPrice.test))
        .where(DiagnosticCentre.id == centre_id)
    )
    centre = result.scalar_one_or_none()
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    return centre

async def create_test(db: AsyncSession, test_in: TestCreate) -> DiagnosticTest:
    test = DiagnosticTest(**test_in.model_dump())
    db.add(test)
    try:
        await db.commit()
        await db.refresh(test)
        return test
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test with this name already exists")

async def get_tests(db: AsyncSession) -> list[DiagnosticTest]:
    result = await db.execute(select(DiagnosticTest))
    return result.scalars().all()

async def associate_test_to_centre(db: AsyncSession, centre_id: uuid.UUID, assoc_in: CentreTestAssociate) -> DiagnosticCentre:
    # Validate centre exists
    await get_centre(db, centre_id)
    
    # Validate test exists
    result = await db.execute(select(DiagnosticTest).where(DiagnosticTest.id == assoc_in.test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
        
    association = CentreTestPrice(
        centre_id=centre_id,
        test_id=assoc_in.test_id,
        price=assoc_in.price
    )
    db.add(association)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test is already associated with this centre")
        
    return await get_centre(db, centre_id)
