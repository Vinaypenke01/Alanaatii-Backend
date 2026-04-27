import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.catalog.models import CatalogItem
from apps.admin_ops.models import SiteSettings, MandatoryQuestion, PricingDayRule, PincodeRule
from apps.content.models import FAQ, SiteContentStep

def run_seed():
    print("🌱 Starting database seeding...")

    # 1. Site Settings
    settings, created = SiteSettings.objects.get_or_create(id=1)
    settings.master_upi_id = "alanaatii@okaxis"
    settings.support_email = "support@alanaatii.com"
    settings.support_whatsapp = "+919876543210"
    settings.maintenance_mode = False
    settings.auto_assign_writers = True
    settings.default_delivery_fee = Decimal('100.00')
    settings.save()
    print("✅ Site Settings initialized.")

    # 2. Catalog Items
    catalog_data = [
        # Themes
        {"category": "letter_theme", "title": "Vintage Elegance", "price": "250.00", "desc": "Classic aged look with burnt edges."},
        {"category": "letter_theme", "title": "Modern Minimalist", "price": "200.00", "desc": "Clean, crisp, and sophisticated."},
        {"category": "letter_theme", "title": "Midnight Stars", "price": "300.00", "desc": "Dark theme with golden ink accents."},
        
        # Styles
        {"category": "style", "title": "Classic Calligraphy", "price": "150.00", "desc": "Beautiful sweeping hand-lettering."},
        {"category": "style", "title": "Vintage Typewriter", "price": "100.00", "desc": "Clean and nostalgic typewriter font style."},
        {"category": "style", "title": "Neat Cursive", "price": "120.00", "desc": "Easily readable, elegant cursive handwriting."},
        
        # Paper
        {"category": "paper", "title": "Premium Ivory (300gsm)", "price": "80.00", "desc": "Thick, luxurious ivory paper."},
        {"category": "paper", "title": "Handmade Deckle Edge", "price": "150.00", "desc": "Artisan paper with rough, feathery edges."},
        
        # Boxes
        {"category": "box", "title": "Velvet Presentation Box", "price": "400.00", "desc": "Premium velvet box for gifting."},
        {"category": "box", "title": "Wooden Keepsake Box", "price": "600.00", "desc": "Engraved wooden box."},
        
        # Gifts
        {"category": "gift", "title": "Vintage Wax Seal", "price": "150.00", "desc": "Custom wax seal stamp on the envelope."},
        {"category": "gift", "title": "Polaroid Photo Print", "price": "100.00", "desc": "Add a classic polaroid photo inside."},
        {"category": "gift", "title": "Custom", "price": "0.00", "desc": "Custom gift (contact support)"},
        
        # Script Packages
        {"category": "package", "title": "Standard Script (300 words)", "price": "500.00", "desc": "Perfect for short, sweet messages."},
        {"category": "package", "title": "Premium Script (600 words)", "price": "900.00", "desc": "Deep, detailed, and poetic expression."},
    ]

    for item in catalog_data:
        CatalogItem.objects.get_or_create(
            category=item['category'],
            title=item['title'],
            defaults={'price': Decimal(item['price']), 'description': item['desc'], 'is_active': True}
        )
    print("✅ Catalog Items populated.")

    # 3. Mandatory Questions (Universal for all orders)
    questions_data = [
        {"text": "What is your relationship with the recipient?", "order": 1},
        {"text": "What is the occasion for this letter? (e.g. Birthday, Apology, Love)", "order": 2},
        {"text": "What are 3 specific things you love or appreciate most about them?", "order": 3},
        {"text": "Is there a specific memory or inside joke you want us to mention?", "order": 4},
        {"text": "What is the core message or feeling you want to convey?", "order": 5},
    ]

    for q in questions_data:
        MandatoryQuestion.objects.get_or_create(
            question_text=q['text'],
            defaults={'display_order': q['order'], 'is_required': True}
        )
    print("✅ Universal Questionnaires added.")

    # 4. Delivery & Pricing Rules
    PricingDayRule.objects.get_or_create(
        days_limit=3, defaults={'extra_charge': Decimal('500.00'), 'label': 'Super Express (3 Days)'}
    )
    PricingDayRule.objects.get_or_create(
        days_limit=7, defaults={'extra_charge': Decimal('250.00'), 'label': 'Express (7 Days)'}
    )

    # Example Pincodes (Hyderabad & Bangalore)
    PincodeRule.objects.get_or_create(zip_prefix="500", defaults={'delivery_fee': Decimal('50.00'), 'region_name': 'Hyderabad (Local)'})
    PincodeRule.objects.get_or_create(zip_prefix="560", defaults={'delivery_fee': Decimal('80.00'), 'region_name': 'Bangalore'})
    print("✅ Pricing and Delivery Rules added.")

    # 5. FAQ
    faqs = [
        {"q": "How long does it take to deliver?", "a": "Standard delivery takes 10-14 days. Express options are available at checkout.", "c": "Delivery"},
        {"q": "Can I review the letter before it is written?", "a": "Yes! Our writers will submit a digital draft for your approval before writing it physically.", "c": "Process"},
        {"q": "Is the handwriting real?", "a": "Absolutely. Every letter is 100% handwritten by our professional calligraphers and writers.", "c": "Product"},
        {"q": "What if I don't like the draft?", "a": "You can request revisions! We offer one free revision to ensure the letter captures your exact feelings.", "c": "Process"},
    ]
    for i, f in enumerate(faqs, 1):
        FAQ.objects.get_or_create(question=f['q'], defaults={'answer': f['a'], 'category': f['c'], 'display_order': i, 'is_active': True})
    
    # 6. How it works steps
    steps = [
        {"title": "Place Your Order", "desc": "Choose your theme, style, and add-ons."},
        {"title": "Fill the Questionnaire", "desc": "Tell us about your relationship and feelings."},
        {"title": "Review the Draft", "desc": "Our writers craft your letter. You review and approve it."},
        {"title": "Handwriting & Delivery", "desc": "We physically write it and ship it to your loved one in premium packaging."}
    ]
    for i, s in enumerate(steps, 1):
        SiteContentStep.objects.get_or_create(
            step_num=i, 
            defaults={'title': s['title'], 'description': s['desc'], 'icon_slug': f'step-{i}'}
        )
    
    print("✅ FAQ & How It Works steps added.")
    print("🎉 Database successfully seeded with Alanaatii premium catalog data!")

if __name__ == '__main__':
    run_seed()
