# 🌐 PUBLIC APIs — No Authentication Required
**Base URL:** `http://localhost:8000/api/v1`

---

## AUTH

### Register Customer
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

---

### Customer Login
**POST** `/auth/user/login/`
```json
{ "email": "rahul@example.com", "password": "MyPass@123" }
```

---

### Writer Login
**POST** `/auth/writer/login/`
```json
{ "email": "writer@alanaatii.com", "password": "Writer@123" }
```

---

### Admin Login
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

## CATALOG

### Browse All Catalog Items
**GET** `/catalog/`
No params — returns all active items grouped by category.

### Filter by Category
**GET** `/catalog/?category=letter_theme`

Category values: `paper` | `box` | `gift` | `style` | `package` | `letter_theme`

---

## RELATION TYPES

### List Relation Categories
**GET** `/relations/`
Returns list like: `["Mother", "Father", "Lover", "Friend", ...]`

---

## QUESTIONNAIRE

### Get Questions for a Relation Type
**GET** `/questions/?relation_type=Mother`
Returns ordered list of questions to show in the order form.

---

## SITE SETTINGS

### Get UPI & Support Info
**GET** `/settings/`
Returns: `{ master_upi_id, support_email, support_whatsapp }`

---

## ORDERS (Guest Checkout)

### Place an Order (Guest — No Login Required)
**POST** `/orders/`

**Script Only:**
```json
{
  "product_type": "script",
  "customer_name": "Rahul Sharma",
  "customer_phone": "9876543210",
  "customer_email": "rahul@example.com",
  "recipient_name": "Priya",
  "recipient_phone": "9123456789",
  "relation": "Lover",
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
  "relation": "Lover",
  "address": "123, MG Road, Flat 4B",
  "city": "Hyderabad",
  "pincode": "500001",
  "delivery_date": "2025-06-15",
  "letter_theme": "<uuid>",
  "text_style": "<uuid>",
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
  "relation": "Lover",
  "address": "123, MG Road",
  "city": "Hyderabad",
  "pincode": "500001",
  "delivery_date": "2025-06-15",
  "letter_theme": "<uuid>",
  "text_style": "<uuid>",
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
Response: `{ valid: true, link_type: "form_fill", order_id: "ORD-12345" }`
