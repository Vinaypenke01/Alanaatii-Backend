# 🛠️ Exhaustive Admin Frontend Guide

This document contains every single endpoint available to the **Admin Role**.

**Base URL:** `http://localhost:8000/api/v1`
**Header:** `Authorization: Bearer <token>`

---

## 1. Authentication & Security

### Login
- **POST** `/auth/admin/login/`
- **Payload:**
  ```json
  { "email": "admin@alanaatii.com", "password": "..." }
  ```

### Refresh Token
- **POST** `/auth/token/refresh/`
- **Payload:**
  ```json
  { "refresh": "<refresh_token_string>" }
  ```

### Logout
- **POST** `/auth/logout/`
- **Payload:**
  ```json
  { "refresh": "<refresh_token_string>" }
  ```

### Create Admin/Sub-Admin
- **POST** `/admin/admins/`
- **Payload:**
  ```json
  {
    "full_name": "Operations Lead",
    "email": "ops@alanaatii.com",
    "role": "manager", // manager | moderator | super_admin
    "password": "..."
  }
  ```

---

## 2. Order & Payment Operations

### Update Order Status & Notes
- **PATCH** `/admin/orders/<id>/status/`
- **Payload:**
  ```json
  {
    "new_status": "out_for_delivery",
    "note": "Public update for customer",
    "internal_notes": "Private staff instructions",
    "tracking_id": "DTDC12345", // Required if status is out_for_delivery
    "courier_name": "DTDC",
    "est_arrival": "2025-06-25"
  }
  ```

### Reassign Order
- **POST** `/admin/orders/<id>/reassign/`
- **Payload:**
  ```json
  { "exclude_writer_id": "<uuid-of-writer-who-rejected>" }
  ```

### Resend Notification
- **POST** `/admin/orders/<id>/resend-notification/`
- **Payload:** `{}`

### Verify Payment
- **POST** `/admin/payments/<uuid>/verify/`
- **Payload:**
  ```json
  { "bank_transaction_id": "SBI-TXN-123456" }
  ```

### Reject Payment
- **POST** `/admin/payments/<uuid>/reject/`
- **Payload:**
  ```json
  { "reason": "Amount does not match screenshot." }
  ```

---

## 3. Catalog & Business Rules

### Create Catalog Item
- **POST** `/admin/catalog/`
- **Payload (Multipart/Form-Data):**
  - `category`: `paper` | `box` | `gift` | `style` | `package` | `letter_theme`
  - `title`: "Premium Ivory"
  - `price`: 150.00
  - `image_url`: [File Binary]
  - `is_active`: true

### Update Catalog Item
- **PUT** `/admin/catalog/<uuid>/`
- **Payload (JSON or Form-Data):**
  ```json
  { "title": "Updated Title", "price": 175.0, "is_active": false }
  ```

### Pricing Rules (Express)
- **POST** `/admin/pricing-rules/`
- **Payload:**
  ```json
  { "days_limit": 7, "extra_charge": 300.0, "label": "Express" }
  ```

### Delivery Rules (Pincode)
- **POST** `/admin/pincode-rules/`
- **Payload:**
  ```json
  { "zip_prefix": "500", "delivery_fee": 80.0, "region_name": "Hyderabad" }
  ```

---

## 4. Questionnaire & Marketing

### Create Question
- **POST** `/admin/questions/`
- **Payload:**
  ```json
  { "question_text": "What is the occasion?", "display_order": 1, "is_required": true }
  ```

### Create Coupon
- **POST** `/admin/coupons/`
- **Payload:**
  ```json
  {
    "code": "ALANAA20",
    "discount_val": 20.0,
    "discount_type": "percentage", // percentage | flat
    "valid_from": "2025-06-01",
    "valid_until": "2025-06-30",
    "max_uses": 100
  }
  ```

---

## 5. Support & Finance

### Initiate Refund
- **POST** `/admin/refunds/`
- **Payload:**
  ```json
  { "order_id": "ORD-123", "amount": 1200.0, "reason": "Customer cancellation" }
  ```

### Process Writer Payout
- **PATCH** `/admin/payouts/<uuid>/process/`
- **Payload:**
  ```json
  { "reference_id": "UPI-PAY-9988" }
  ```

### Reply to Support Message
- **PATCH** `/admin/support/<id>/`
- **Payload:**
  ```json
  { "admin_reply": "We have updated your delivery address.", "status": "responded" }
  ```
