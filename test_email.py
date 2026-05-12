import os
import resend
from decouple import config

# Load the API Key directly from your .env
api_key = "re_8oVSa9j1_5sFKNKW9wqyH948bJ9J5GJY8"
resend.api_key = api_key

print(f"Testing Resend API with key: {api_key[:10]}...")

try:
    params = {
        "from": "info@digitalcore.co.in",
        "to": "roadwaycars61@gmail.com",
        "subject": "Alanaatii - Domain Verification Test",
        "text": "If you are reading this, your digitalcore.co.in domain is verified and working!"
    }
    
    r = resend.Emails.send(params)
    print("✅ SUCCESS!")
    print(f"Email ID: {r.get('id')}")
    print("Please check your inbox (roadwaycars61@gmail.com) including the SPAM folder.")

except Exception as e:
    print("❌ FAILED")
    print(f"Error Message: {str(e)}")
