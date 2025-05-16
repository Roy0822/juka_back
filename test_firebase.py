#!/usr/bin/env python3
"""
Test script to verify Firebase initialization works
"""
import os
import sys

print(f"Working directory: {os.getcwd()}")
print(f"Service account file exists: {os.path.exists('Juka Firebase Admin SDK.json')}")

try:
    import firebase_admin
    from firebase_admin import credentials
    
    print("Firebase admin package imported successfully")
    
    # Try to initialize Firebase with the service account file
    cred = credentials.Certificate("Juka Firebase Admin SDK.json")
    firebase_app = firebase_admin.initialize_app(cred)
    
    print(f"Firebase initialized successfully: {firebase_app.name}")
    print("FCM setup is working properly!")
    
except Exception as e:
    print(f"Error initializing Firebase: {str(e)}")
    sys.exit(1) 