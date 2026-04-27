# 🌐 Frontend Guest & Public Guide

This guide details all APIs that can be called **without an Authorization token**. Use these for the Landing Page, Product Browsing, and Login screens.

**Base URL:** `http://localhost:8000/api/v1`
**Header:** None required.

---

## 1. Landing Page & Content

### Fetch "How it Works" Steps
- **GET** `/site-steps/`
- **Response:** List of steps with titles, descriptions, and order.

### List FAQs
- **GET** `/faq/`
- **Response:** List of question/answer objects.

### List Customer Reviews
- **GET** `/reviews/`
- **Response:** List of approved reviews with ratings and comments.

### Public Site Settings
- **GET** `/settings/`
- **Response:**
  ```json
  {
    "master_upi_id": "alanaatii@sbi",
    "support_email": "hello@alanaatii.com",
    "support_whatsapp": "+919876543210"
  }
  ```

---

## 2. Product Discovery

### Browse Catalog
- **GET** `/catalog/`
- **Query Params:** `?category=paper` | `?category=box` | `?category=gift`
- **Response:** List of purchasable items.

### Fetch Questionnaire Questions (Preview)
- **GET** `/questions/`
- **Response:** List of questions that will be asked after purchase.

---

## 3. Entry Actions

### Submit Support/Contact Form
- **POST** `/support/`
- **Payload:**
  ```json
  {
    "full_name": "Interested Guest",
    "email": "guest@example.com",
    "subject": "Inquiry about bulk orders",
    "message": "Do you offer discounts for wedding invites?"
  }
  ```

### Validate Coupon (Check validity only)
- **POST** `/coupons/validate/`
- **Payload:**
  ```json
  { "code": "WELCOME10", "order_total": 1200.0 }
  ```

---

## 4. Authentication Entry (The Handshake)

### Google OAuth Login
- **POST** `/auth/user/google/`
- **Payload:** `{ "access_token": "..." }`
- **Returns:** Tokens to be used in all subsequent "Authenticated" calls.

### Login / Register (Traditional)
- **POST** `/auth/user/login/` | **POST** `/auth/user/register/`
- **Payloads:** Email, Password, Name, etc.
- **Note:** Only active if `.env` has `AUTH_MODE_PASSWORD=True`.

---

## 5. Utility

### Resolve Secure Email Link
Used when a user clicks a "Fill Details" button in their email.
- **GET** `/secure-link/?token=<link_token>`
- **Response:** 
  ```json
  { "action": "form_fill", "order_id": "ORD-123", "is_valid": true }
  ```
