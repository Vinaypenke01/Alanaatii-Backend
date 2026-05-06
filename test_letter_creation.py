import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.catalog.models import CatalogItem, CatalogCategory

def run_test():
    print("--- 🧪 Testing Catalog Item Creation ---")
    
    # 1. Create Boxes
    print("Creating Boxes...")
    box1 = CatalogItem.objects.create(
        category=CatalogCategory.BOX,
        title="Trunck pette Test Box",
        price=500.00,
        is_active=True
    )
    box2 = CatalogItem.objects.create(
        category=CatalogCategory.BOX,
        title="Mayabazar Test Box",
        price=800.00,
        is_active=True
    )
    print(f"✅ Created Boxes: {box1.title}, {box2.title}")

    # 2. Create Normal Letter (Fits all boxes, requires custom length)
    print("\nCreating Normal Letter...")
    letter1 = CatalogItem.objects.create(
        category=CatalogCategory.LETTER_THEME,
        title="Normal vintage Utharam Test",
        price=150.00,
        requires_custom_length=True,
        fits_all_boxes=True
    )
    print(f"✅ Created Letter: {letter1.title} | Fits all boxes: {letter1.fits_all_boxes} | Requires custom length: {letter1.requires_custom_length}")

    # 3. Create Restricted Letter (Fits specific boxes)
    print("\nCreating Restricted Letter...")
    letter2 = CatalogItem.objects.create(
        category=CatalogCategory.LETTER_THEME,
        title="Gnyapakam Utharam Test",
        price=200.00,
        requires_custom_length=False,
        fits_all_boxes=False
    )
    
    # Assign compatible boxes
    letter2.compatible_boxes.add(box1)
    
    print(f"✅ Created Letter: {letter2.title} | Fits all boxes: {letter2.fits_all_boxes}")
    print(f"✅ Compatible Boxes for {letter2.title}: {[b.title for b in letter2.compatible_boxes.all()]}")

    print("\n🎉 Test passed successfully! Cleaning up test data...")
    # Clean up test data
    box1.delete()
    box2.delete()
    letter1.delete()
    letter2.delete()
    print("🧹 Cleanup complete.")

if __name__ == '__main__':
    run_test()
