from django.conf import settings
import os

def check():
    print("--- 🔍 Settings Diagnostic ---")
    print(f"DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
    print(f"CLOUDINARY_CLOUD_NAME: {settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')}")
    print(f"CLOUDINARY_API_KEY: {settings.CLOUDINARY_STORAGE.get('API_KEY')[:4]}***")
    
    # Check if 'cloudinary_storage' is in INSTALLED_APPS
    print(f"Cloudinary in APPS: {'cloudinary_storage' in settings.INSTALLED_APPS}")
    
    # Check if MEDIA_URL is /media/
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    
if __name__ == "__main__":
    check()
