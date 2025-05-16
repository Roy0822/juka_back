import os
import uuid
import time
import mimetypes
import aiofiles
from fastapi import UploadFile, HTTPException, status
import boto3
from botocore.exceptions import ClientError
from urllib.parse import urljoin

from app.core.config import settings

# Try to import python-magic, but provide a fallback method if it's not available
try:
    import magic
    HAS_MAGIC_LIB = True
except ImportError:
    HAS_MAGIC_LIB = False
    import imghdr  # Built-in module for image detection
    print("Warning: python-magic not available, using simplified image validation")

class FileStorageService:
    """Service for handling file storage operations"""
    
    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """Get the file extension from the filename"""
        return os.path.splitext(filename)[1].lower()[1:]
    
    @staticmethod
    def _is_allowed_file(filename: str) -> bool:
        """Check if the file extension is allowed"""
        extension = FileStorageService._get_file_extension(filename)
        return extension.lower() in settings.ALLOWED_EXTENSIONS
    
    @staticmethod
    def _is_safe_file(file_content: bytes) -> bool:
        """Check if the file content is safe (is actually an image)"""
        if HAS_MAGIC_LIB:
            # Use magic library if available
            mime = magic.Magic(mime=True)
            file_mime = mime.from_buffer(file_content)
            return file_mime.startswith('image/')
        else:
            # Fallback method using imghdr
            img_type = imghdr.what(None, file_content)
            return img_type is not None and img_type in ['jpeg', 'png', 'gif', 'bmp']
    
    @staticmethod
    def _generate_unique_filename(filename: str) -> str:
        """Generate a unique filename to avoid collisions"""
        extension = FileStorageService._get_file_extension(filename)
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4().hex)
        return f"{timestamp}_{unique_id}.{extension}"
    
    @staticmethod
    async def upload_file(file: UploadFile, folder_path: str = None) -> str:
        """
        Upload a file to storage and return its public URL
        
        Args:
            file: The file to upload
            folder_path: Optional subfolder path within the main upload folder
            
        Returns:
            str: The public URL of the uploaded file
            
        Raises:
            HTTPException: If the file is not allowed or upload fails
        """
        # Validate file type by extension
        if not FileStorageService._is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed. Allowed types: " + ", ".join(settings.ALLOWED_EXTENSIONS)
            )
        
        # Read file content for validation and upload
        contents = await file.read()
        
        # Validate file content
        if not FileStorageService._is_safe_file(contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content appears to be invalid or not an image"
            )
        
        # Reset file position to beginning for upload
        await file.seek(0)
        
        # Generate a unique filename
        unique_filename = FileStorageService._generate_unique_filename(file.filename)
        
        # Set subfolder if provided
        if folder_path:
            unique_filename = f"{folder_path}/{unique_filename}"
        
        # Choose storage method based on configuration
        if settings.STORAGE_TYPE == "s3":
            return await FileStorageService._upload_to_s3(file, unique_filename, contents)
        else:
            return await FileStorageService._upload_to_local(file, unique_filename, contents)
    
    @staticmethod
    async def _upload_to_local(file: UploadFile, filename: str, contents: bytes) -> str:
        """Upload file to local storage"""
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        
        # If filename contains subfolders, create them
        if "/" in filename:
            subfolder_path = os.path.join(settings.UPLOAD_FOLDER, os.path.dirname(filename))
            os.makedirs(subfolder_path, exist_ok=True)
        
        # Full path to save the file
        file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
        
        # Save the file
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(contents)
        
        # Return public URL
        if settings.PUBLIC_URL_PREFIX:
            return urljoin(settings.PUBLIC_URL_PREFIX, filename)
        else:
            # For development, return a relative URL
            return f"/uploads/{filename}"
    
    @staticmethod
    async def _upload_to_s3(file: UploadFile, filename: str, contents: bytes) -> str:
        """Upload file to S3 storage"""
        if not settings.S3_BUCKET or not settings.S3_REGION:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 storage is not properly configured"
            )
        
        try:
            # Configure S3 client
            s3_client = boto3.client(
                's3',
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY
            )
            
            # Set content type based on file extension
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            # Upload to S3
            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=filename,
                Body=contents,
                ContentType=content_type,
                ACL='public-read'
            )
            
            # Return public URL
            if settings.PUBLIC_URL_PREFIX:
                return urljoin(settings.PUBLIC_URL_PREFIX, filename)
            else:
                return f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{filename}"
                
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload failed: {str(e)}"
            )
    
    @staticmethod
    async def delete_file(file_url: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_url: The URL of the file to delete
            
        Returns:
            bool: True if the file was deleted, False otherwise
        """
        # Extract filename from URL
        filename = os.path.basename(file_url)
        
        # Check if URL has a path component
        if '/' in file_url:
            path_parts = file_url.split('/')
            # Find the uploads part and take everything after
            if 'uploads' in path_parts:
                uploads_index = path_parts.index('uploads')
                filename = '/'.join(path_parts[uploads_index+1:])
            # For S3 URLs, take everything after the bucket name
            elif settings.S3_BUCKET and settings.S3_BUCKET in file_url:
                bucket_index = path_parts.index(settings.S3_BUCKET)
                filename = '/'.join(path_parts[bucket_index+1:])
        
        # Choose deletion method based on configuration
        if settings.STORAGE_TYPE == "s3":
            return await FileStorageService._delete_from_s3(filename)
        else:
            return await FileStorageService._delete_from_local(filename)
    
    @staticmethod
    async def _delete_from_local(filename: str) -> bool:
        """Delete file from local storage"""
        file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False
    
    @staticmethod
    async def _delete_from_s3(filename: str) -> bool:
        """Delete file from S3 storage"""
        if not settings.S3_BUCKET or not settings.S3_REGION:
            return False
        
        try:
            # Configure S3 client
            s3_client = boto3.client(
                's3',
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY
            )
            
            # Delete from S3
            s3_client.delete_object(
                Bucket=settings.S3_BUCKET,
                Key=filename
            )
            
            return True
                
        except ClientError:
            return False 