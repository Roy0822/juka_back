from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.file_storage import FileStorageService
from app.models.user import User

router = APIRouter()

@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    folder: str = None,
    db: Session = Depends(get_db)
):
    """
    Upload an image file and get its public URL
    
    Args:
        file: The image file to upload
        folder: Optional subfolder to organize uploads (e.g., 'profiles', 'campaigns')
        
    Returns:
        dict: URL of the uploaded image
    """
    # 添加調試輸出
    print(f"DEBUG: 收到圖片上傳請求，文件名: {file.filename}, 內容類型: {file.content_type}")
    
    # Validate that the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate folder path if provided
    if folder and not folder.isalnum() and not all(c.isalnum() or c == '_' for c in folder):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder name can only contain alphanumeric characters and underscores"
        )
    
    try:
        # Upload the image 
        url = await FileStorageService.upload_file(file, folder)
        
        # 添加調試輸出
        print(f"DEBUG: 圖片上傳成功，URL: {url}")
        
        # Return the URL
        return {"url": url}
        
    except Exception as e:
        # Log the error and return a generic error message
        print(f"DEBUG: 上傳圖片時出錯: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )

@router.delete("/image")
async def delete_image(
    url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an image by its URL
    
    Args:
        url: The URL of the image to delete
        
    Returns:
        dict: Success message
    """
    # Check if the URL is empty
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image URL is required"
        )
    
    try:
        # Delete the image
        result = await FileStorageService.delete_file(url)
        
        if result:
            return {"success": True, "message": "Image deleted successfully"}
        else:
            return {"success": False, "message": "Image not found or could not be deleted"}
            
    except Exception as e:
        # Log the error and return a generic error message
        print(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        ) 