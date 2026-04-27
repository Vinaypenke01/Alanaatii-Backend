# 🎁 Exhaustive Customer Frontend Guide

This document contains every single endpoint available to the **Customer Role**.

**Base URL:** `http://localhost:8000/api/v1`

---

## 1. Authentication

### Google OAuth Login
- **POST** `/auth/user/google/`
- **Payload:**
  ```json
  { "access_token": "GOOGLE_JWT_FROM_FIREBASE_OR_GCP" }
  ```

### Traditional Registration (If active)
- **POST** `/auth/user/register/`
- **Payload:**
  ```json
  {
    "full_name": "Rahul Sharma",
    "email": "rahul@example.com",
    "password": "...",
    "password_confirm": "...",
    "phone_wa": "9876543210"
  }
  ```

---

## 2. Checkout & Fulfillment (Auth Required)

### Step 1: Place Order
- **POST** `/orders/`
- **Payload (Letter + Gift Box example):**
  ```json
  {
    "product_type": "letterBoxGift",
    "customer_name": "Rahul Sharma",
    "customer_email": "rahul@example.com",
    "customer_phone": "9876543210",
    "recipient_name": "Priya",
    "address": "123, MG Road",
    "city": "Hyderabad",
    "pincode": "500001",
    "delivery_date": "2025-06-25",
    "letter_theme": "<uuid>",
    "text_style": "<uuid>",
    "box": "<uuid>",
    "gift": "<uuid>",
    "coupon_code": "SAVE10"
  }
  ```

### Step 2: Upload Payment Screenshot
- **POST** `/orders/<id>/upload-screenshot/`
- **Payload (Multipart/Form-Data):**
  - `screenshot`: [File Binary]

### Step 3: Submit Questionnaire
- **POST** `/orders/<id>/questionnaire/`
- **Payload:**
  ```json
  {
    "answers": [
      { "question_id": 1, "answer": "Father" },
      { "question_id": 2, "answer": "Retirement gift" },
      { "question_id": 3, "answer": "He loves gardening." }
    ]
  }
  ```

### Step 4: Approve / Revise Script
- **POST** `/orders/<id>/script-action/`
- **Payload (Approve):**
  ```json
  { "action": "approve" }
  ```
- **Payload (Revise):**
  ```json
  { "action": "revise", "feedback": "Make it sound more formal." }
  ```

---

## 3. Account Management

### View Profile
- **GET** `/user/profile/`
- **Response:** `{ "id": "...", "full_name": "...", "email": "...", "phone_wa": "..." }`

### Update Profile
- **PUT** `/user/profile/`
- **Payload:** `{ "full_name": "Rahul New Name", "phone_wa": "9876543210" }`

### Add Address
- **POST** `/user/addresses/`
- **Payload:**
  ```json
  {
    "full_name": "Home",
    "address_line1": "Flat 402, Skyline Apartments",
    "city": "Mumbai",
    "pincode": "400001",
    "is_default": true
  }
  ```

### Get Specific Address
- **GET** `/user/addresses/<uuid>/`

### Update Specific Address
- **PUT** `/user/addresses/<uuid>/`
- **Payload:** `{ "address_line1": "Updated Lane", "is_default": false }`

### Delete Address
- **DELETE** `/user/addresses/<uuid>/`
- **Payload:** `{}`

### Submit Review
- **POST** `/reviews/submit/`
- **Payload:**
  ```json
  {
    "order_id": "ORD-12345",
    "rating": 5,
    "comment": "The calligraphy was breathtaking!"
  }
  ```

### Validate Coupon (Public)
- **POST** `/coupons/validate/`
- **Payload:**
  ```json
  { "code": "SAVE20", "order_total": 1500.0 }
  ```
