from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.repositories.business_repository import BusinessRepository
from app.models.user import User as UserModel
from app.schemas.business import Business, BusinessCreate, BusinessUpdate

router = APIRouter()

@router.get("/", response_model=List[Business])
async def get_businesses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all businesses
    """
    business_repo = BusinessRepository(db)
    businesses = business_repo.get_businesses(skip, limit)
    return businesses

@router.get("/{business_id}", response_model=Business)
async def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a business by ID
    """
    business_repo = BusinessRepository(db)
    business = business_repo.get_business_by_id(business_id)
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此商家"
        )
        
    return business

@router.post("/", response_model=Business)
async def create_business(
    business_data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new business (admin only in production)
    """
    from app.core.config import settings
    
    # In production, restrict to admin
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅開發環境或管理員可用"
        )
        
    business_repo = BusinessRepository(db)
    business = business_repo.create_business(business_data)
    return business

@router.put("/{business_id}", response_model=Business)
async def update_business(
    business_id: int,
    business_data: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a business (admin only in production)
    """
    from app.core.config import settings
    
    # In production, restrict to admin
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅開發環境或管理員可用"
        )
        
    business_repo = BusinessRepository(db)
    
    # Check if business exists
    business = business_repo.get_business_by_id(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此商家"
        )
        
    # Update business
    updated_business = business_repo.update_business(business_id, business_data)
    return updated_business

@router.delete("/{business_id}", response_model=dict)
async def delete_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a business (admin only in production)
    """
    from app.core.config import settings
    
    # In production, restrict to admin
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅開發環境或管理員可用"
        )
        
    business_repo = BusinessRepository(db)
    
    # Check if business exists
    business = business_repo.get_business_by_id(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此商家"
        )
        
    # Delete business
    success = business_repo.delete_business(business_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除商家失敗"
        )
        
    return {"status": "success", "message": "成功刪除商家"}

@router.post("/nearby", response_model=List[Business])
async def get_nearby_businesses(
    latitude: float,
    longitude: float,
    radius: float = 5.0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get businesses near a location
    """
    business_repo = BusinessRepository(db)
    businesses = business_repo.get_nearby_businesses(
        latitude,
        longitude,
        radius,
        limit
    )
    
    return businesses 