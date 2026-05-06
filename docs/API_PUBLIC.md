# 🌐 PUBLIC APIs — No Authentication Required
**Base URL:** `http://localhost:8000/api/v1`

> **Auth Mode Toggle** — controlled by `AUTH_MODE_PASSWORD` in `.env`:
> - `True` → Email/password endpoints active. Google OAuth returns `403`.
> - `False` → Google OAuth active. Email/password endpoints return `403`.
>
> ⚠️ Writer and Admin logins are **always** password-based, regardless of this flag.

---

## AUTH

### ① Register Customer *(AUTH_MODE_PASSWORD=True only)*
**POST** `/auth/user/register/`
```json
{
  "full_name": "Rahul Sharma",
  "email": "rahul@example.com",
  "phone_wa": "9876543210",
  "password": "MyPass@123",
  "password_confirm": "MyPass@123"
}
```
**Success `201`:**
```json
{
  "message": "Account created successfully.",
  "tokens": { "access": "...", "refresh": "..." },
  "user": { "id": "...", "full_name": "Rahul Sharma", "email": "rahul@example.com" }
}
```
**When disabled `403`:**
```json
{
  "error": true,
  "code": "AUTH_MODE_DISABLED",
  "message": "Password registration is disabled. Please use Google Sign-In.",
  "google_endpoint": "/api/v1/auth/user/google/"
}
```

---

### ② Customer Login *(AUTH_MODE_PASSWORD=True only)*
**POST** `/auth/user/login/`
```json
{ "email": "rahul@example.com", "password": "MyPass@123" }
```
**Success `200`:**
```json
{
  "message": "Login successful.",
  "tokens": { "access": "...", "refresh": "..." },
  "user": { "id": "...", "full_name": "Rahul Sharma", "email": "rahul@example.com" }
}
```
**When disabled `403`:**
```json
{
  "error": true,
  "code": "AUTH_MODE_DISABLED",
  "message": "Password login is disabled. Please use Google Sign-In.",
  "google_endpoint": "/api/v1/auth/user/google/"
}
```

---

### ③ Google OAuth Login / Register *(AUTH_MODE_PASSWORD=False only)*
**POST** `/auth/user/google/`

The frontend obtains `id_token` from Google Sign-In SDK (`@react-oauth/google`) and posts it here. The backend verifies it server-side against Google's public keys — never trusts the frontend payload blindly.

```json
{ "id_token": "<google_id_token_from_frontend>" }
```
**Success — Existing user `200`:**
```json
{
  "message": "Google login successful.",
  "is_new_account": false,
  "tokens": { "access": "...", "refresh": "..." },
  "user": { "id": "...", "full_name": "Rahul Sharma", "email": "rahul@gmail.com" }
}
```
**Success — New account auto-created `201`:**
```json
{
  "message": "Google login successful.",
  "is_new_account": true,
  "tokens": { "access": "...", "refresh": "..." },
  "user": { "id": "...", "full_name": "Rahul Sharma", "email": "rahul@gmail.com" }
}
```
> `is_new_account: true` → show welcome/onboarding screen on the frontend.
> `is_new_account: false` → go straight to the dashboard.

**When disabled `403`:**
```json
{
  "error": true,
  "code": "AUTH_MODE_DISABLED",
  "message": "Google OAuth is disabled. Please use email and password to log in.",
  "login_endpoint": "/api/v1/auth/user/login/"
}
```

---

### Writer Login *(always password-based)*
**POST** `/auth/writer/login/`
```json
{ "email": "writer@alanaatii.com", "password": "Writer@123" }
```

---

### Admin Login *(always password-based)*
**POST** `/auth/admin/login/`
```json
{ "email": "admin@alanaatii.com", "password": "Admin@1234" }
```

---

### Refresh Access Token
**POST** `/auth/token/refresh/`
```json
{ "refresh": "<refresh_token>" }
```

---

### Logout
**POST** `/auth/logout/` *(requires Bearer token)*
```json
{ "refresh": "<refresh_token>" }
```

---

## CATALOG

### Browse All Catalog Items
**GET** `/catalog/`
No params — returns all active items grouped by category.

### Filter by Category
**GET** `/catalog/?category=letter_theme`

Category values: `paper` | `box` | `gift` | `style` | `package` | `letter_theme`

---

## QUESTIONNAIRE

### Get Universal Questions
**GET** `/questions/`
Returns the list of mandatory questions for all orders (e.g., Relationship, Occasion, Memories).

---

## SITE SETTINGS

### Get UPI & Support Info
**GET** `/settings/`
Returns: `{ master_upi_id, support_email, support_whatsapp }`

---

## ORDERS (Authenticated Only)

### Place an Order
**POST** `/orders/`
*(Requires Auth: Bearer Token from Google OAuth)*

**Script Only:**
```json
{
  "product_type": "script",
  "customer_name": "Rahul Sharma",
  "customer_phone": "9876543210",
  "customer_email": "rahul@example.com",
  "recipient_name": "Priya",
  "recipient_phone": "9123456789",
  "relation": "Lover / Partner",
  "message_content": "Write a heartfelt anniversary letter.",
  "special_notes": "She loves poetry.",
  "express_script": false,
  "script_package": "<uuid-of-package-catalog-item>"
}
```

**Letter Only:**
```json
{
  "product_type": "letter",
  "customer_name": "Rahul Sharma",
  "customer_phone": "9876543210",
  "customer_email": "rahul@example.com",
  "recipient_name": "Priya",
  "recipient_phone": "9123456789",
  "primary_contact": "sender",
  "relation": "Lover / Partner",
  "address": "123, MG Road, Flat 4B",
  "city": "Hyderabad",
  "pincode": "500001",
  "delivery_date": "2025-06-15",
  "letter_theme": "<uuid>",
  "text_style": "<uuid>",
  "custom_letter_length": "6 feet",
  "coupon_code": ""
}
```

**Letter + Box + Gift:**
```json
{
  "product_type": "letterBoxGift",
  "customer_name": "Rahul Sharma",
  "customer_phone": "9876543210",
  "customer_email": "rahul@example.com",
  "recipient_name": "Priya",
  "recipient_phone": "9123456789",
  "primary_contact": "sender",
  "relation": "Lover / Partner",
  "address": "123, MG Road",
  "city": "Hyderabad",
  "pincode": "500001",
  "delivery_date": "2025-06-15",
  "letter_theme": "<uuid>",
  "text_style": "<uuid>",
  "custom_letter_length": "6 feet",
  "box": "<uuid>",
  "gift": "<uuid>",
  "coupon_code": "SAVE20"
}
```

---

## COUPON

### Validate Coupon Code
**POST** `/coupons/validate/`
```json
{ "code": "SAVE20", "order_total": 1500.00 }
```
Response: `{ "discount_amount": 300.0, "code": "SAVE20" }`

---

## CONTENT

### Published Reviews
**GET** `/reviews/`

### Submit a Review
**POST** `/reviews/submit/`
```json
{
  "customer_name": "Priya",
  "rating": 5,
  "content": "Absolutely loved the letter!",
  "order_id": "ORD-12345"
}
```

### FAQ List
**GET** `/faq/`

### How It Works Steps
**GET** `/site-steps/`

### Contact / Support Message
**POST** `/support/`
```json
{
  "name": "Anjali",
  "email": "anjali@example.com",
  "phone": "9876543210",
  "message": "I need help with my order."
}
```

---

## SECURE LINK (From Email)

### Validate Email Link Token
**GET** `/secure-link/?token=<token>`
Validates one-time token from email link.
Response: `{ "valid": true, "link_type": "form_fill", "order_id": "ORD-12345" }`
