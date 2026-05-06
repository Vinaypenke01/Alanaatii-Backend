# 🔧 ADMIN APIs — Role: admin / super_admin
**Base URL:** `http://localhost:8000/api/v1`
**Header required on ALL requests:**
```
Authorization: Bearer <admin_access_token>
```
Get your token from `POST /auth/admin/login/`

---

## DASHBOARD

### Analytics Summary
**GET** `/admin/analytics/`

Returns: total orders, total revenue, pending payments, orders by status, orders by type, recent 10 orders.

---

## ORDERS

### All Orders (Filterable)
**GET** `/admin/orders/`

| Query Param | Example | Description |
|-------------|---------|-------------|
| `status` | `?status=payment_pending` | Filter by status |
| `search` | `?search=rahul` | Search by name, email, order ID, or **Bank Txn ID** |
| `page` | `?page=2` | Page number |
| `page_size` | `?page_size=20` | Items per page |

**All status values:**
`payment_pending` `payment_rejected` `awaiting_details` `order_placed` `assigned_to_writer` `assignment_rejected` `accepted_by_writer` `script_submitted` `customer_review` `revision_requested` `approved` `under_writing` `out_for_delivery` `delivered` `cancelled` `refunded`

---

### Order Detail (Admin)
**GET** `/admin/orders/<order_id>/`

Returns full order + status history + all script versions + transaction log.

---

### Update Order Status
**PATCH** `/admin/orders/<order_id>/status/`

Basic status update:
```json
{
  "new_status": "under_writing",
  "note": "Script approved. Physical writing started.",
  "internal_notes": "Writer is using ivory paper as requested."
}
```
*Note: `internal_notes` is private and not visible to customers.*

When shipping (`out_for_delivery`):
```json
{
  "new_status": "out_for_delivery",
  "tracking_id": "DTDC1234567",
  "courier_name": "DTDC",
  "est_arrival": "2025-06-20",
  "note": "Dispatched via DTDC courier."
}
```

When delivered:
```json
{
  "new_status": "delivered",
  "note": "Delivered successfully."
}
```

---

### Cancel Order (Admin)
**POST** `/admin/orders/<order_id>/cancel/`
Body: `{}`

---

### Reassign Order to Another Writer
**POST** `/admin/orders/<order_id>/reassign/`
```json
{ "exclude_writer_id": "<uuid-of-writer-who-declined>" }
```
Auto-picks the next least-loaded available writer.

### Resend Status Notification
**POST** `/admin/orders/<order_id>/resend-notification/`
Body: `{}`
Manually re-triggers the email for the current order status (e.g., resends the Questionnaire link).

---

## PAYMENT VERIFICATION

### Pending Payments List
**GET** `/admin/payments/`

| Query Param | Description |
|-------------|-------------|
| `?status=pending` | Default — show pending |
| `?status=verified` | Already verified |
| `?status=rejected` | Rejected payments |

---

### Verify Payment
**POST** `/admin/payments/<transaction_uuid>/verify/`
```json
{ "bank_transaction_id": "SBI-TXN-12345678" }
```

Triggers:
- Transaction status → `verified`
- `bank_transaction_id` is saved for auditing
- Order status → `awaiting_details`
- Email sent to customer to fill questionnaire

---

### Reject Payment
**POST** `/admin/payments/<transaction_uuid>/reject/`
```json
{ "reason": "Screenshot is blurry and amount does not match." }
```

Triggers:
- Transaction status → `rejected`
- Order status → `payment_rejected`
- Email sent to customer

---

## REFUNDS

### Refund List
**GET** `/admin/refunds/`

---

### Create Refund
**POST** `/admin/refunds/`
```json
{
  "order_id": "ORD-12345",
  "amount": 1200.00,
  "reason": "Customer cancelled before writing started."
}
```

---

### Update Refund Status
**PATCH** `/admin/refunds/<uuid>/`
```json
{ "status": "completed" }
```
Status options: `pending` | `completed` | `rejected`

---

## WRITER MANAGEMENT

### List All Writers
**GET** `/admin/writers/`

| Query Param | Description |
|-------------|-------------|
| `?status=active` | Active writers |
| `?status=inactive` | Inactive writers |
| `?search=meera` | Search by name/email |

---

### Create Writer Account
**POST** `/admin/writers/`
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

### Writer Detail
**GET** `/admin/writers/<writer_uuid>/`

---

### Update Writer
**PUT** `/admin/writers/<writer_uuid>/`
```json
{
  "status": "inactive",
  "phone": "9999999999"
}
```

---

### Delete Writer
**DELETE** `/admin/writers/<writer_uuid>/`
> ⚠️ Blocked if writer has active assignments.

---

### Writer's Assignment History
**GET** `/admin/writers/<writer_uuid>/assignments/`

---

## CATALOG MANAGEMENT

### List Catalog (Admin View — includes inactive)
**GET** `/admin/catalog/`
Filter: `?category=paper`

---

### Create Catalog Item
**POST** `/admin/catalog/`
> Use `Content-Type: multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | string | ✅ | `paper` `box` `gift` `style` `package` `letter_theme` |
| `title` | string | ✅ | Item name |
| `price` | decimal | ✅ | e.g. `150.00` |
| `description` | string | ❌ | Optional description |
| `is_active` | boolean | ❌ | Default: `true` |
| `image_url` | file | ❌ | Upload image |
| `requires_custom_length`| boolean| ❌ | Default: `false`. If true, frontend asks user for custom length/height. |
| `fits_all_boxes` | boolean | ❌ | Default: `true`. If false, specify `compatible_boxes`. |
| `compatible_boxes` | array | ❌ | Array of box UUIDs this item fits into. |

---

### Update Catalog Item
**PUT** `/admin/catalog/<uuid>/`
```json
{
  "title": "Premium Ivory Paper",
  "price": 175.00,
  "is_active": true,
  "fits_all_boxes": true,
  "compatible_boxes": []
}
```

---

### Delete Catalog Item
**DELETE** `/admin/catalog/<uuid>/`

---

## SITE SETTINGS

### View Settings
**GET** `/admin/settings/`

---

### Update Settings
**PUT** `/admin/settings/`
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

## PRICING RULES

### List Rules
**GET** `/admin/pricing-rules/`

### Create Rule
**POST** `/admin/pricing-rules/`
```json
{
  "days_limit": 7,
  "extra_charge": 300.00,
  "label": "Express (within 7 days)"
}
```

### Update Rule
**PUT** `/admin/pricing-rules/<id>/`
```json
{ "extra_charge": 350.00 }
```

### Delete Rule
**DELETE** `/admin/pricing-rules/<id>/`

---

## PINCODE DELIVERY RULES

### List Rules
**GET** `/admin/pincode-rules/`

### Create Rule
**POST** `/admin/pincode-rules/`
```json
{
  "zip_prefix": "500",
  "delivery_fee": 80.00,
  "region_name": "Hyderabad"
}
```

### Update Rule
**PUT** `/admin/pincode-rules/<id>/`

### Delete Rule
**DELETE** `/admin/pincode-rules/<id>/`

---

## QUESTIONNAIRE BUILDER

### List Questions
**GET** `/admin/questions/`

### Create Question
**POST** `/admin/questions/`
```json
{
  "question_text": "What is your relationship with the recipient?",
  "display_order": 1,
  "is_required": true
}
```

### Update Question
**PUT** `/admin/questions/<id>/`
```json
{ "question_text": "Updated question text.", "display_order": 2 }
```

### Delete Question
**DELETE** `/admin/questions/<id>/`

---

## COUPONS

### List Coupons
**GET** `/admin/coupons/`

### Create Coupon
**POST** `/admin/coupons/`
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
`discount_type`: `percentage` or `flat`

### Update Coupon
**PUT** `/admin/coupons/<uuid>/`
```json
{ "is_active": false }
```

### Delete Coupon
**DELETE** `/admin/coupons/<uuid>/`

---

## PAYOUTS

### List All Payouts
**GET** `/admin/payouts/`
Filter: `?writer_id=<writer_uuid>`

### Create Payout
**POST** `/admin/payouts/`
```json
{
  "writer_id": "<writer-uuid>",
  "amount": 2500.00,
  "period_start": "2025-06-01",
  "period_end": "2025-06-30"
}
```

### Mark Payout as Processed
**PATCH** `/admin/payouts/<uuid>/process/`
```json
{ "reference_id": "UPI-TXN-987654" }
```

---

## SUPPORT MESSAGES

### List Messages
**GET** `/admin/support/`
Filter: `?status=new` | `?status=read` | `?status=responded`

### Reply to Message
**PATCH** `/admin/support/<id>/`
```json
{
  "status": "responded",
  "admin_reply": "Hi Anjali, your order has been updated. Please check your dashboard."
}
```

---

## CONTENT MODERATION

### List All Reviews
**GET** `/admin/reviews/`

### Publish / Unpublish Review
**PATCH** `/admin/reviews/<id>/`
```json
{ "is_published": true }
```

### Delete Review
**DELETE** `/admin/reviews/<id>/`

---

### FAQ Management
**GET** `/admin/faq/`

**POST** `/admin/faq/`
```json
{
  "question": "How long does delivery take?",
  "answer": "We deliver within 7-10 business days across India.",
  "category": "Delivery",
  "display_order": 1,
  "is_active": true
}
```

**PUT** `/admin/faq/<id>/`
```json
{ "answer": "Updated delivery time: 5-7 business days." }
```

**DELETE** `/admin/faq/<id>/`

---

## AUDIT LOGS

### View Audit Trail
**GET** `/admin/audit-logs/`
Returns last 100 system actions by all roles.

---

## ADMIN ACCOUNTS (Super Admin Only)

### Create Admin Account
**POST** `/admin/admins/`
```json
{
  "full_name": "Ops Manager",
  "email": "ops@alanaatii.com",
  "role": "manager",
  "password": "Ops@1234"
}
```
`role` options: `super_admin` | `manager` | `moderator`

---

## LOGOUT

### Logout
**POST** `/auth/logout/`
```json
{ "refresh": "<refresh_token>" }
```

---

## ERROR RESPONSE FORMAT

All errors return a consistent JSON shape:
```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "email: This field is required.",
  "details": { "email": ["This field is required."] }
}
```

| HTTP | Code |
|------|------|
| 400 | `VALIDATION_ERROR` |
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 500 | `INTERNAL_SERVER_ERROR` |
