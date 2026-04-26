# Alanaatii API — Postman Reference
**Base URL:** `http://localhost:8000/api/v1`
**Auth Header:** `Authorization: Bearer <access_token>` (for protected routes)
**Content-Type:** `application/json` (unless file upload — use `multipart/form-data`)

---

## 1. AUTHENTICATION (All Roles)

### 1.1 Customer Register
- **POST** `/auth/user/register/`
- **Auth:** None
```json
{
  "full_name": "Rahul Sharma",
  "email": "rahul@example.com",
  "phone_wa": "9876543210",
  "password": "MyPass@123",
  "password_confirm": "MyPass@123"
}
```
**Response:** `201` — tokens + user object

---

### 1.2 Customer Login
- **POST** `/auth/user/login/`
- **Auth:** None
```json
{
  "email": "rahul@example.com",
  "password": "MyPass@123"
}
```
**Response:** `200` — `{ tokens: { access, refresh }, user: {...} }`

---

### 1.3 Writer Login
- **POST** `/auth/writer/login/`
- **Auth:** None
```json
{
  "email": "writer@alanaatii.com",
  "password": "Writer@123"
}
```
**Response:** `200` — tokens + writer object

---

### 1.4 Admin Login
- **POST** `/auth/admin/login/`
- **Auth:** None
```json
{
  "email": "admin@alanaatii.com",
  "password": "Admin@1234"
}
```
**Response:** `200` — tokens + admin object

---

### 1.5 Refresh Token
- **POST** `/auth/token/refresh/`
- **Auth:** None
```json
{
  "refresh": "<refresh_token>"
}
```
**Response:** `200` — `{ access: "..." }`

---

### 1.6 Logout
- **POST** `/auth/logout/`
- **Auth:** Bearer Token (any role)
```json
{
  "refresh": "<refresh_token>"
}
```
**Response:** `200` — `{ message: "Logged out successfully." }`

---

## 2. PUBLIC ENDPOINTS (No Auth)

### 2.1 Browse Catalog
- **GET** `/catalog/`
- **Auth:** None
- **Query Params:**
  - `?category=paper` — filter by category
  - Valid categories: `paper`, `box`, `gift`, `style`, `package`, `letter_theme`
- **Example:** `GET /api/v1/catalog/?category=letter_theme`

---

### 2.2 Get Relation Categories
- **GET** `/relations/`
- **Auth:** None
- Returns list of relation types (Mother, Father, Lover, Friend, etc.)

---

### 2.3 Get Questionnaire for a Relation
- **GET** `/questions/?relation_type=Mother`
- **Auth:** None
- **Query Params:** `?relation_type=Mother`

---

### 2.4 Get Site Settings (UPI / Support)
- **GET** `/settings/`
- **Auth:** None
- Returns `master_upi_id`, `support_email`, `support_whatsapp`

---

### 2.5 Validate Coupon
- **POST** `/coupons/validate/`
- **Auth:** None
```json
{
  "code": "SAVE20",
  "order_total": 1500.00
}
```
**Response:** `{ "discount_amount": 300.0, "code": "SAVE20" }`

---

### 2.6 Get Published Reviews
- **GET** `/reviews/`
- **Auth:** None

---

### 2.7 Submit Review
- **POST** `/reviews/submit/`
- **Auth:** None
```json
{
  "customer_name": "Priya",
  "rating": 5,
  "content": "Absolutely loved the letter! So beautifully written.",
  "order_id": "ORD-12345"
}
```

---

### 2.8 Get FAQ
- **GET** `/faq/`
- **Auth:** None

---

### 2.9 Get How It Works Steps
- **GET** `/site-steps/`
- **Auth:** None

---

### 2.10 Submit Support / Contact Form
- **POST** `/support/`
- **Auth:** None
```json
{
  "name": "Anjali",
  "email": "anjali@example.com",
  "phone": "9876543210",
  "message": "I need help with my order."
}
```

---

### 2.11 Validate Secure Email Link
- **GET** `/secure-link/?token=<token>`
- **Auth:** None
- **Query Params:** `?token=abc123xyz` (from email link)
- **Response:** `{ valid: true, link_type: "form_fill", order_id: "ORD-12345" }`

---

## 3. CUSTOMER PORTAL (Role: user)

**All requests need:** `Authorization: Bearer <user_access_token>`

---

### 3.1 Place Order (Guest or Logged In)
- **POST** `/orders/`
- **Auth:** Optional (Bearer token if logged in, else no auth)
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
  "message_content": "Write a heartfelt letter about our 2-year journey.",
  "special_notes": "She loves poetry.",
  "express_script": false,
  "address": "123, MG Road, Flat 4B",
  "city": "Hyderabad",
  "pincode": "500001",
  "delivery_date": "2025-06-15",
  "paper_quantity": 1,
  "payment_screenshot": "",
  "coupon_code": "SAVE20",
  "letter_theme": "<uuid-of-catalog-item>",
  "text_style": "<uuid-of-catalog-item>",
  "paper": null,
  "box": null,
  "gift": null,
  "script_package": null
}
```

**Product type options:**
- `script` — Only Script (needs `script_package` id)
- `letterPaper` — Only Paper (needs `paper` id, `paper_quantity`)
- `letter` — Letter only (needs `letter_theme`, `text_style`)
- `letterBox` — Letter + Box (needs `letter_theme`, `text_style`, `box`)
- `letterBoxGift` — Letter + Box + Gift (needs all above + `gift`)

**Response:** `201` — `{ order: { id: "ORD-XXXXX", status: "payment_pending", ... } }`

---

### 3.2 Upload Payment Screenshot
- **POST** `/orders/<order_id>/upload-screenshot/`
- **Auth:** Bearer (user)
- **Content-Type:** `multipart/form-data`
- **Form Field:** `screenshot` (image file — JPG/PNG of UPI screenshot)
- **Example URL:** `POST /api/v1/orders/ORD-12345/upload-screenshot/`

---

### 3.3 My Orders List
- **GET** `/orders/my/`
- **Auth:** Bearer (user)
- **Query Params:**
  - `?page=1` — pagination
  - `?page_size=10`

---

### 3.4 Order Detail
- **GET** `/orders/<order_id>/`
- **Auth:** Bearer (user)
- **Example:** `GET /api/v1/orders/ORD-12345/`
- **Response:** Full order + status history + script versions + latest transaction

---

### 3.5 Submit Questionnaire (Relationship Details)
- **POST** `/orders/<order_id>/questionnaire/`
- **Auth:** Bearer (user)
```json
{
  "answers": [
    { "question_id": 1, "answer": "We met in college in 2019." },
    { "question_id": 2, "answer": "She loves sunsets and poetry." },
    { "question_id": 3, "answer": "Our first trip was to Coorg." }
  ]
}
```

---

### 3.6 Approve Script
- **POST** `/orders/<order_id>/script-action/`
- **Auth:** Bearer (user)
```json
{
  "action": "approve"
}
```

---

### 3.7 Request Script Revision
- **POST** `/orders/<order_id>/script-action/`
- **Auth:** Bearer (user)
```json
{
  "action": "revision",
  "feedback": "Please make it more poetic and add a reference to our trip to Manali."
}
```

---

### 3.8 Cancel Order
- **POST** `/orders/<order_id>/cancel/`
- **Auth:** Bearer (user)
- **Body:** (empty) `{}`
- **Note:** Only works if order is in early stages (before writer accepts)

---

### 3.9 View Profile
- **GET** `/user/profile/`
- **Auth:** Bearer (user)

---

### 3.10 Update Profile
- **PUT** `/user/profile/`
- **Auth:** Bearer (user)
```json
{
  "full_name": "Rahul Sharma",
  "phone_wa": "9876543210",
  "address_def": "123, MG Road",
  "city_def": "Hyderabad",
  "pincode_def": "500001",
  "birthday": "1995-06-15",
  "anniversary": "2020-02-14"
}
```

---

### 3.11 List Saved Addresses
- **GET** `/user/addresses/`
- **Auth:** Bearer (user)

---

### 3.12 Add Address
- **POST** `/user/addresses/`
- **Auth:** Bearer (user)
```json
{
  "label": "Home",
  "receiver_name": "Priya Sharma",
  "phone": "9123456789",
  "address": "456, Banjara Hills",
  "city": "Hyderabad",
  "pincode": "500034",
  "is_primary": true
}
```

---

### 3.13 Update Address
- **PUT** `/user/addresses/<uuid>/`
- **Auth:** Bearer (user)
```json
{
  "label": "Office",
  "address": "789, HITEC City",
  "city": "Hyderabad",
  "pincode": "500081"
}
```

---

### 3.14 Delete Address
- **DELETE** `/user/addresses/<uuid>/`
- **Auth:** Bearer (user)
- **Body:** None

---

### 3.15 My Notifications
- **GET** `/notifications/`
- **Auth:** Bearer (user)

---

### 3.16 Mark Notification as Read
- **POST** `/notifications/<id>/read/`
- **Auth:** Bearer (user)
- **Body:** `{}`

---

## 4. WRITER PORTAL (Role: writer)

**All requests need:** `Authorization: Bearer <writer_access_token>`

---

### 4.1 Writer Profile
- **GET** `/writer/profile/`
- **Auth:** Bearer (writer)

---

### 4.2 Update Writer Profile
- **PUT** `/writer/profile/`
- **Auth:** Bearer (writer)
```json
{
  "full_name": "Meera Krishnan",
  "phone": "9876541230",
  "address": "12, Jubilee Hills, Hyderabad",
  "languages": ["Telugu", "English", "Hindi"]
}
```

---

### 4.3 My Assignments
- **GET** `/writer/assignments/`
- **Auth:** Bearer (writer)
- **Query Params:** `?status=pending` or `?status=accepted` or `?status=declined`

---

### 4.4 Accept Assignment
- **POST** `/writer/assignments/<id>/accept/`
- **Auth:** Bearer (writer)
- **Body:** `{}`

---

### 4.5 Decline Assignment
- **POST** `/writer/assignments/<id>/decline/`
- **Auth:** Bearer (writer)
```json
{
  "reason": "I am already at full capacity this week."
}
```

---

### 4.6 My Assigned Orders
- **GET** `/writer/orders/`
- **Auth:** Bearer (writer)
- **Query Params:** `?status=accepted`

---

### 4.7 Get/Save Draft (Auto-save)
- **GET** `/writer/orders/<order_id>/draft/`
- **Auth:** Bearer (writer)

- **PUT** `/writer/orders/<order_id>/draft/`
- **Auth:** Bearer (writer)
```json
{
  "draft_content": "Dear Priya, It has been two wonderful years..."
}
```

---

### 4.8 Submit Final Script
- **POST** `/writer/orders/<order_id>/submit-script/`
- **Auth:** Bearer (writer)
```json
{
  "content": "Dear Priya,\n\nIt has been two magical years since we met...\n\nWith all my love,\nRahul",
  "writer_note": "I kept the tone warm and personal as requested."
}
```

---

### 4.9 My Payouts
- **GET** `/writer/payouts/`
- **Auth:** Bearer (writer)

---

### 4.10 Writer Stats
- **GET** `/writer/stats/`
- **Auth:** Bearer (writer)
- **Response:** `{ active_jobs, completed_jobs, pending_payouts }`

---

### 4.11 Writer Notifications
- **GET** `/notifications/`
- **Auth:** Bearer (writer)

---

## 5. ADMIN PORTAL (Role: admin)

**All requests need:** `Authorization: Bearer <admin_access_token>`

---

### 5.1 Analytics Dashboard
- **GET** `/admin/analytics/`
- **Auth:** Bearer (admin)
- **Response:** total orders, revenue, pending payments, orders by status/type, recent orders

---

### 5.2 All Orders (Filterable)
- **GET** `/admin/orders/`
- **Auth:** Bearer (admin)
- **Query Params:**
  - `?status=payment_pending`
  - `?status=assigned_to_writer`
  - `?search=rahul` — search by name/email/order ID
  - `?page=1&page_size=20`

**Status values:**
`payment_pending`, `payment_rejected`, `awaiting_details`, `order_placed`, `assigned_to_writer`, `assignment_rejected`, `accepted_by_writer`, `script_submitted`, `customer_review`, `revision_requested`, `approved`, `under_writing`, `out_for_delivery`, `delivered`, `cancelled`, `refunded`

---

### 5.3 Order Detail (Admin)
- **GET** `/admin/orders/<order_id>/`
- **Auth:** Bearer (admin)
- Returns full order + history + scripts + transaction

---

### 5.4 Update Order Status
- **PATCH** `/admin/orders/<order_id>/status/`
- **Auth:** Bearer (admin)
```json
{
  "new_status": "under_writing",
  "note": "Script approved. Physical writing started."
}
```

For delivery status include tracking:
```json
{
  "new_status": "out_for_delivery",
  "tracking_id": "DTDC1234567",
  "courier_name": "DTDC",
  "est_arrival": "2025-06-20",
  "note": "Shipped via DTDC."
}
```

---

### 5.5 Cancel Order (Admin)
- **POST** `/admin/orders/<order_id>/cancel/`
- **Auth:** Bearer (admin)
- **Body:** `{}`

---

### 5.6 Reassign Order to Another Writer
- **POST** `/admin/orders/<order_id>/reassign/`
- **Auth:** Bearer (admin)
```json
{
  "exclude_writer_id": "<uuid-of-writer-who-declined>"
}
```

---

### 5.7 Pending Payments List
- **GET** `/admin/payments/`
- **Auth:** Bearer (admin)
- **Query Params:** `?status=pending` or `?status=verified` or `?status=rejected`

---

### 5.8 Verify Payment
- **POST** `/admin/payments/<transaction_uuid>/verify/`
- **Auth:** Bearer (admin)
- **Body:** `{}`

---

### 5.9 Reject Payment
- **POST** `/admin/payments/<transaction_uuid>/reject/`
- **Auth:** Bearer (admin)
```json
{
  "reason": "Screenshot is blurry and amount does not match."
}
```

---

### 5.10 Refund List
- **GET** `/admin/refunds/`
- **Auth:** Bearer (admin)

---

### 5.11 Create Refund
- **POST** `/admin/refunds/`
- **Auth:** Bearer (admin)
```json
{
  "order_id": "ORD-12345",
  "amount": 1200.00,
  "reason": "Customer cancelled before writing started."
}
```

---

### 5.12 Update Refund Status
- **PATCH** `/admin/refunds/<uuid>/`
- **Auth:** Bearer (admin)
```json
{
  "status": "completed"
}
```
Status options: `pending`, `completed`, `rejected`

---

### 5.13 Writer Management — List
- **GET** `/admin/writers/`
- **Auth:** Bearer (admin)
- **Query Params:** `?status=active` or `?status=inactive`, `?search=meera`

---

### 5.14 Create Writer
- **POST** `/admin/writers/`
- **Auth:** Bearer (admin)
```json
{
  "full_name": "Meera Krishnan",
  "email": "meera@alanaatii.com",
  "phone": "9876541230",
  "phone_alt": "9876541231",
  "address": "12, Jubilee Hills, Hyderabad",
  "languages": ["Telugu", "English"],
  "password": "Writer@123"
}
```

---

### 5.15 Writer Detail
- **GET** `/admin/writers/<uuid>/`
- **Auth:** Bearer (admin)

---

### 5.16 Update Writer
- **PUT** `/admin/writers/<uuid>/`
- **Auth:** Bearer (admin)
```json
{
  "status": "inactive",
  "phone": "9999999999"
}
```

---

### 5.17 Delete Writer
- **DELETE** `/admin/writers/<uuid>/`
- **Auth:** Bearer (admin)
- **Note:** Blocked if writer has active assignments

---

### 5.18 Writer's Assignments (Admin View)
- **GET** `/admin/writers/<uuid>/assignments/`
- **Auth:** Bearer (admin)

---

### 5.19 Catalog — List (Admin)
- **GET** `/admin/catalog/`
- **Auth:** Bearer (admin)
- **Query Params:** `?category=paper`

---

### 5.20 Create Catalog Item
- **POST** `/admin/catalog/`
- **Auth:** Bearer (admin)
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `category` (string): `paper` | `box` | `gift` | `style` | `package` | `letter_theme`
  - `title` (string): "Premium Ivory Paper"
  - `price` (decimal): 150.00
  - `description` (string, optional)
  - `is_active` (boolean): true
  - `image_url` (file, optional): upload image

---

### 5.21 Update Catalog Item
- **PUT** `/admin/catalog/<uuid>/`
- **Auth:** Bearer (admin)
```json
{
  "title": "Premium Ivory Paper",
  "price": 175.00,
  "is_active": true
}
```

---

### 5.22 Delete Catalog Item
- **DELETE** `/admin/catalog/<uuid>/`
- **Auth:** Bearer (admin)

---

### 5.23 Relation Categories (Admin)
- **GET** `/admin/relations/`
- **POST** `/admin/relations/`
```json
{ "name": "Best Friend", "is_active": true }
```
- **DELETE** `/admin/relations/<id>/`

---

### 5.24 Site Settings — View
- **GET** `/admin/settings/`
- **Auth:** Bearer (admin)

---

### 5.25 Site Settings — Update
- **PUT** `/admin/settings/`
- **Auth:** Bearer (admin)
```json
{
  "master_upi_id": "alanaatii@okaxis",
  "support_email": "support@alanaatii.com",
  "support_whatsapp": "+91-9876543210",
  "maintenance_mode": false,
  "auto_assign_writers": true,
  "default_delivery_fee": 100.00
}
```

---

### 5.26 Pricing Day Rules
- **GET** `/admin/pricing-rules/`
- **POST** `/admin/pricing-rules/`
```json
{
  "days_limit": 7,
  "extra_charge": 300.00,
  "label": "Express (within 7 days)"
}
```
- **PUT** `/admin/pricing-rules/<id>/` — same payload (partial)
- **DELETE** `/admin/pricing-rules/<id>/`

---

### 5.27 Pincode Delivery Rules
- **GET** `/admin/pincode-rules/`
- **POST** `/admin/pincode-rules/`
```json
{
  "zip_prefix": "500",
  "delivery_fee": 80.00,
  "region_name": "Hyderabad"
}
```
- **PUT** `/admin/pincode-rules/<id>/`
- **DELETE** `/admin/pincode-rules/<id>/`

---

### 5.28 Mandatory Questions (Questionnaire Builder)
- **GET** `/admin/questions/?relation_type=Mother`
- **POST** `/admin/questions/`
```json
{
  "relation_type": "Mother",
  "question_text": "What is your favourite memory with your mother?",
  "display_order": 1,
  "is_required": true
}
```
- **PUT** `/admin/questions/<id>/`
- **DELETE** `/admin/questions/<id>/`

---

### 5.29 Coupons
- **GET** `/admin/coupons/`
- **POST** `/admin/coupons/`
```json
{
  "code": "SAVE20",
  "discount_val": 20.00,
  "discount_type": "percentage",
  "max_uses": 100,
  "valid_from": "2025-06-01",
  "valid_until": "2025-06-30",
  "min_order": 500.00,
  "is_active": true
}
```
- `discount_type`: `percentage` or `flat`
- **PUT** `/admin/coupons/<uuid>/`
- **DELETE** `/admin/coupons/<uuid>/`

---

### 5.30 Payouts — List & Create
- **GET** `/admin/payouts/?writer_id=<uuid>`
- **POST** `/admin/payouts/`
```json
{
  "writer_id": "<writer-uuid>",
  "amount": 2500.00,
  "period_start": "2025-06-01",
  "period_end": "2025-06-30"
}
```

---

### 5.31 Process Payout
- **PATCH** `/admin/payouts/<uuid>/process/`
- **Auth:** Bearer (admin)
```json
{
  "reference_id": "UPI-TXN-987654"
}
```

---

### 5.32 Support Messages
- **GET** `/admin/support/?status=new`
- Status options: `new`, `read`, `responded`

- **PATCH** `/admin/support/<id>/`
```json
{
  "status": "responded",
  "admin_reply": "Hi Anjali, your order has been updated. Please check your dashboard."
}
```

---

### 5.33 Reviews (Admin Moderation)
- **GET** `/admin/reviews/`
- **PATCH** `/admin/reviews/<id>/` — approve/unpublish
```json
{ "is_published": true }
```
- **DELETE** `/admin/reviews/<id>/`

---

### 5.34 FAQ (Admin)
- **GET** `/admin/faq/`
- **POST** `/admin/faq/`
```json
{
  "question": "How long does delivery take?",
  "answer": "We deliver within 7-10 business days across India.",
  "category": "Delivery",
  "display_order": 1,
  "is_active": true
}
```
- **PUT** `/admin/faq/<id>/`
- **DELETE** `/admin/faq/<id>/`

---

### 5.35 Audit Logs
- **GET** `/admin/audit-logs/`
- **Auth:** Bearer (admin)
- Returns last 100 actions by admins/writers

---

### 5.36 Create Admin Account (Super Admin only)
- **POST** `/admin/admins/`
- **Auth:** Bearer (super_admin only)
```json
{
  "full_name": "Ops Manager",
  "email": "ops@alanaatii.com",
  "role": "manager",
  "password": "Ops@1234"
}
```
- `role` options: `super_admin`, `manager`, `moderator`

---

## 6. ERROR RESPONSE FORMAT

All errors return:
```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "email: This field is required.",
  "details": { "email": ["This field is required."] }
}
```

| HTTP Code | code |
|-----------|------|
| 400 | VALIDATION_ERROR |
| 401 | UNAUTHORIZED |
| 403 | FORBIDDEN |
| 404 | NOT_FOUND |
| 429 | RATE_LIMITED |
| 500 | INTERNAL_SERVER_ERROR |

---

## 7. POSTMAN SETUP

### Environment Variables
Set these in Postman Environment:

| Variable | Value |
|----------|-------|
| `base_url` | `http://localhost:8000/api/v1` |
| `user_token` | *(paste from login response)* |
| `writer_token` | *(paste from login response)* |
| `admin_token` | *(paste from login response)* |

### Using Variables in Requests
- **URL:** `{{base_url}}/orders/`
- **Header:** `Authorization: Bearer {{admin_token}}`

### Quick Start Test Sequence
1. `POST /auth/admin/login/` → copy `access` token → set `admin_token`
2. `GET /admin/analytics/` — verify admin auth works
3. `POST /admin/catalog/` — add a Letter Theme item
4. `POST /admin/questions/` — add questions for "Lover" relation
5. `POST /auth/user/register/` → copy `access` token → set `user_token`
6. `POST /orders/` — place an order (use catalog item IDs from step 3)
7. `GET /admin/payments/?status=pending` — see the pending payment
8. `POST /admin/payments/<txn_id>/verify/` — verify payment
9. `GET /admin/orders/?status=assigned_to_writer` — see the auto-assigned order
10. `POST /auth/writer/login/` → set `writer_token`
11. `GET /writer/assignments/?status=pending` — see new assignment
12. `POST /writer/assignments/<id>/accept/`
13. `POST /writer/orders/<order_id>/submit-script/` — submit script
14. `POST /orders/<order_id>/script-action/` with `{"action":"approve"}` — approve
15. `PATCH /admin/orders/<order_id>/status/` with `{"new_status":"delivered"}`
