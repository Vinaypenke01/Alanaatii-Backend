import os
import django
from django.core.files.base import ContentFile
from django.utils import timezone
from apps.catalog.models import CatalogItem, CatalogCategory
from apps.accounts.models import Admin

def run_test():
    print("🚀 Starting Cloudinary Configuration Test...")
    
    # 1. Get or Create a Super Admin for the record
    admin = Admin.objects.filter(role='super_admin').first()
    if not admin:
        print("❌ No Admin found. Please create an admin first (see README).")
        return

    # 2. Read the real image file
    image_path = r"e:\Client-Projects\alanaatii\Full_stack\Alanaatii-Backend\docs\E34-1.jpg"
    print(f"📸 Reading real image from {image_path}...")
    
    try:
        with open(image_path, "rb") as f:
            image_content = f.read()
            
        image_name = f"test_cloudinary_real_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg"
        
        # 3. Create a Catalog Item (This triggers the Cloudinary upload)
        print("☁️ Attempting upload to Cloudinary...")
        item = CatalogItem.objects.create(
            category=CatalogCategory.PAPER,
            title=f"Cloudinary Test Real {timezone.now().strftime('%H:%M:%S')}",
            price=150.0,
            created_by=admin
        )
        
        # Manually save the image to trigger storage engine
        item.image_url.save(image_name, ContentFile(image_content))
        
        print("\n✅ SUCCESS!")
        print(f"🔗 Cloudinary URL: {item.image_url.url}")
        
        # Extract public ID for dashboard search
        try:
            public_id = item.image_url.name
            print(f"🆔 Dashboard Public ID: {public_id}")
        except:
            pass
        
        if "res.cloudinary.com" in item.image_url.url:
            print("🌟 VERIFIED: Images are being stored on Cloudinary CDN.")
        else:
            print("⚠️ WARNING: URL does not look like a Cloudinary link. Check settings.py.")
            
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        print("\nPossible fixes:")
        print("- Check if CLOUDINARY_API_KEY is correct in .env")
        print("- Ensure 'cloudinary' and 'cloudinary_storage' are in INSTALLED_APPS")
        print("- Verify internet connection to Cloudinary API")

if __name__ == "__main__":
    run_test()
