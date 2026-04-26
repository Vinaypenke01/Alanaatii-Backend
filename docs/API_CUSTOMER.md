# 👤 CUSTOMER APIs — Role: user
**Base URL:** `http://localhost:8000/api/v1`
**Header required on ALL requests:**
```
Authorization: Bearer <user_access_token>
```
Get your token from `POST /auth/user/login/`

---

## PROFILE

### View My Profile
**GET** `/user/profile/`

---

### Update My Profile
**PUT** `/user/profile/`
```json
{
  "full_name": "Rahul Sharma",
  "phone_wa": "9876543210",
  "address_def": "123, MG Road, Flat 4B",
  "city_def": "Hyderabad",
  "pincode_def": "500001",
  "birthday": "1995-06-15",
  "anniversary": "2020-02-14"
}
```

---

## SAVED ADDRESSES

### List My Addresses
**GET** `/user/addresses/`

---

### Add New Address
**POST** `/user/addresses/`
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

### Update Address
**PUT** `/user/addresses/<address-uuid>/`
```json
{
  "label": "Office",
  "address": "789, HITEC City",
  "city": "Hyderabad",
  "pincode": "500081",
  "is_primary": false
}
```

---

### Delete Address
**DELETE** `/user/addresses/<address-uuid>/`
No body needed.

---

## ORDERS

### My Orders List
**GET** `/orders/my/`

Query params (optional):
- `?page=1`
- `?page_size=10`

---

### Order Detail
**GET** `/orders/<order_id>/`
Example: `GET /api/v1/orders/ORD-12345/`

Returns: full order + status history + script versions + latest transaction

---

### Upload Payment Screenshot (After placing order)
**POST** `/orders/<order_id>/upload-screenshot/`

> ⚠️ Use `Content-Type: multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `screenshot` | File | JPG/PNG of UPI payment screenshot |

---

### Submit Relationship Questionnaire
**POST** `/orders/<order_id>/questionnaire/`

Required after payment is verified. Unlocks writer assignment.
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

### Approve Script
**POST** `/orders/<order_id>/script-action/`
```json
{ "action": "approve" }
```
Response: `{ message: "Script approved!", status: "approved" }`

---

### Request Script Revision
**POST** `/orders/<order_id>/script-action/`
```json
{
  "action": "revision",
  "feedback": "Please make it more poetic and reference our trip to Manali."
}
```
Response: `{ message: "Revision request submitted.", status: "revision_requested" }`

---

### Cancel Order
**POST** `/orders/<order_id>/cancel/`
Body: `{}`

> ⚠️ Only works if order is in: `payment_pending`, `payment_rejected`, `awaiting_details`, `order_placed`, or `assigned_to_writer` (before writer accepts).

---

## NOTIFICATIONS

### My Notifications
**GET** `/notifications/`
Returns last 50 notifications for the logged-in customer.

---

### Mark Notification as Read
**POST** `/notifications/<notification_id>/read/`
Body: `{}`

---

### Mark All Notifications as Read
**PATCH** `/notifications/read-all/`
Body: `{}`

---

## LOGOUT

### Logout
**POST** `/auth/logout/`
```json
{ "refresh": "<refresh_token>" }
```
