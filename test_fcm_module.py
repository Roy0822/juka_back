#!/usr/bin/env python3
"""
Test script to verify the FCM module initialization
"""
import os
import sys

print(f"Working directory: {os.getcwd()}")
print(f"Service account file exists: {os.path.exists('Juka Firebase Admin SDK.json')}")

try:
    # Import the FCM module and check initialization
    from app.core.fcm import firebase_initialized, FCMService
    
    print(f"Firebase initialized via module: {firebase_initialized}")
    
    # Try to send a test notification to a dummy token
    async def test_send():
        response = await FCMService.send_notification(
            token="dummy_token_for_testing",
            title="Test Notification",
            body="This is a test from the FCM module",
            data={"test": "true"}
        )
        print(f"FCM send response: {response}")
    
    # Run the async function
    import asyncio
    asyncio.run(test_send())
    
except Exception as e:
    print(f"Error testing FCM module: {str(e)}")
    sys.exit(1) 