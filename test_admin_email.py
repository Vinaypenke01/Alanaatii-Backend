import os
import django
import resend
from decouple import config

# Initialize Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from utils.email import send_admin_new_order_email

# Mock Order object
class MockOrder:
    def __init__(self):
        self.id = "ORD-TEST-123"
        self.customer_name = "Test Customer"
        self.customer_email = "customer@example.com"
        self.product_type = "Luxury Letter"
        self.total_amount = 500

print("--- Admin Email Diagnostic Test ---")
admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'Not Set')
sender_email = settings.DEFAULT_FROM_EMAIL

print(f"Recipient (Admin): {admin_email}")
print(f"Sender (From): {sender_email}")
print(f"API Key: {settings.RESEND_API_KEY[:10]}...")

order = MockOrder()

try:
    print("\nAttempting to send admin notification...")
    # Note: Using synchronous call to capture errors immediately
    from utils.email import _send_email_sync
    
    subject = f'New Order Pending Payment Verification – #{order.id}'
    body = (
        f'A new order has been placed and requires payment verification.\n\n'
        f'Order ID: {order.id}\n'
        f'Customer: {order.customer_name} ({order.customer_email})\n'
        f'Product: {order.product_type}\n'
        f'Amount: ₹{order.total_amount}\n\n'
        f'Verify Payment: {settings.FRONTEND_URL}/admin/payments\n\n'
        f'Alanaatii Admin System'
    )
    
    _send_email_sync(admin_email, subject, body)
    print("\n✅ Check the terminal above for any '❌ Resend Error'.")
    print("If no error appeared, the email was successfully handed off to Resend.")
    
except Exception as e:
    print(f"\n❌ CRITICAL SYSTEM ERROR: {str(e)}")
