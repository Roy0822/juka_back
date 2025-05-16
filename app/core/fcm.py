import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings
import json
import os
import tempfile
from typing import List, Dict, Any, Optional

# Firebase Admin SDK initialization
firebase_initialized = False

try:
    # Check for Firebase Admin SDK JSON file in project root
    service_account_path = "Juka Firebase Admin SDK.json"
    
    if os.path.exists(service_account_path):
        # Initialize with the service account file
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
        print(f"Initialized Firebase with service account file: {service_account_path}")
    # Method 1: Service Account JSON (recommended)
    elif settings.FCM_AUTH_METHOD == "service_account" and settings.FCM_SERVICE_ACCOUNT_JSON:
        # Create a temporary file for the service account JSON if provided as a string
        if isinstance(settings.FCM_SERVICE_ACCOUNT_JSON, str):
            try:
                # Try to parse the JSON string
                service_account_dict = json.loads(settings.FCM_SERVICE_ACCOUNT_JSON)
                
                # Create a temporary file to store the JSON
                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    json.dump(service_account_dict, temp_file)
                
                # Initialize with the temporary file
                cred = credentials.Certificate(temp_file_path)
                firebase_admin.initialize_app(cred)
                firebase_initialized = True
                
                # Clean up the temporary file
                os.unlink(temp_file_path)
                print("Initialized Firebase with service account JSON")
            except json.JSONDecodeError:
                # If it's not a valid JSON string, assume it's a file path
                if os.path.exists(settings.FCM_SERVICE_ACCOUNT_JSON):
                    cred = credentials.Certificate(settings.FCM_SERVICE_ACCOUNT_JSON)
                    firebase_admin.initialize_app(cred)
                    firebase_initialized = True
                    print(f"Initialized Firebase with service account file: {settings.FCM_SERVICE_ACCOUNT_JSON}")
    
    # Method 2: Legacy Server Key (deprecated but still supported)
    elif settings.FCM_AUTH_METHOD == "server_key" and settings.FCM_SERVER_KEY:
        # Use the legacy server key method - less secure but still works
        cred = credentials.Certificate(json.loads(settings.FCM_SERVER_KEY))
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
        print("Initialized Firebase with server key (legacy method)")
    
    # Initialize with default app in development mode
    elif settings.APP_ENV == "development":
        # For development, we can use the default app without credentials
        firebase_admin.initialize_app()
        firebase_initialized = True
        print("Initialized Firebase with default app (development mode)")
    else:
        print("No Firebase credentials provided")

except Exception as e:
    # In development mode, we can continue without FCM
    if settings.APP_ENV == "development":
        print(f"Development mode: FCM initialization skipped. Error: {str(e)}")
    else:
        # In production, we should log the error but not crash
        print(f"Error initializing Firebase: {str(e)}")

class FCMService:
    @staticmethod
    async def send_notification(
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Send notification to a single device
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data to send
            
        Returns:
            Message ID
        """
        if not firebase_initialized:
            print(f"DEV MODE: Would send notification to {token}")
            print(f"Title: {title}")
            print(f"Body: {body}")
            print(f"Data: {data}")
            return "dev-message-id"

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        
        try:
            response = messaging.send(message)
            return response
        except Exception as e:
            print(f"FCM send error: {str(e)}")
            if settings.APP_ENV == "development":
                return "dev-message-id"
            raise

    @staticmethod
    async def send_multicast(
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> messaging.BatchResponse:
        """
        Send notification to multiple devices
        
        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data to send
            
        Returns:
            Batch response
        """
        if not firebase_initialized:
            print(f"DEV MODE: Would send multicast to {len(tokens)} devices")
            print(f"Title: {title}")
            print(f"Body: {body}")
            print(f"Data: {data}")
            return None

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
        )
        
        try:
            response = messaging.send_multicast(message)
            return response
        except Exception as e:
            print(f"FCM multicast send error: {str(e)}")
            if settings.APP_ENV == "development":
                return None
            raise 