# ✍️ WRITER APIs — Role: writer
**Base URL:** `http://localhost:8000/api/v1`
**Header required on ALL requests:**
```
Authorization: Bearer <writer_access_token>
```
Get your token from `POST /auth/writer/login/`

---

## PROFILE

### View My Writer Profile
**GET** `/writer/profile/`

---

### Update My Writer Profile
**PUT** `/writer/profile/`
```json
{
  "full_name": "Meera Krishnan",
  "phone": "9876541230",
  "address": "12, Jubilee Hills, Hyderabad",
  "languages": ["Telugu", "English", "Hindi"]
}
```

---

## STATS

### My Performance Stats
**GET** `/writer/stats/`

Response:
```json
{
  "active_jobs": 2,
  "completed_jobs": 15,
  "pending_payouts": 1
}
```

---

## ASSIGNMENTS

### My Assignments (All)
**GET** `/writer/assignments/`

Filter by status (optional):
- `GET /writer/assignments/?status=pending`
- `GET /writer/assignments/?status=accepted`
- `GET /writer/assignments/?status=declined`

---

### Accept an Assignment
**POST** `/writer/assignments/<assignment_id>/accept/`
Body: `{}`

Triggers:
- Order status → `accepted_by_writer`
- Email notification to admin

---

### Decline an Assignment
**POST** `/writer/assignments/<assignment_id>/decline/`
```json
{ "reason": "I am already at full capacity this week." }
```
> `reason` must be at least 5 characters.

Triggers:
- Order status → `assignment_rejected`
- Admin is notified to reassign

---

## ORDERS (Writer View)

### My Active Assigned Orders
**GET** `/writer/orders/`

Filter by status (optional):
- `GET /writer/orders/?status=accepted`

---

### Get Auto-save Draft
**GET** `/writer/orders/<order_id>/draft/`

Returns the last saved draft content (if any).

---

### Save Draft (Auto-save)
**PUT** `/writer/orders/<order_id>/draft/`
```json
{
  "draft_content": "Dear Priya, It has been two wonderful years since we first met..."
}
```

---

### Submit Final Script
**POST** `/writer/orders/<order_id>/submit-script/`
```json
{
  "content": "Dear Priya,\n\nIt has been two magical years since we met at that little café in Koramangala...\n\nWith all my love,\nRahul",
  "writer_note": "I kept the tone warm and personal. Used the memory of their Coorg trip as a highlight."
}
```

Triggers:
- Order status → `script_submitted`
- Customer receives email to review the script

---

## PAYOUTS

### My Payout History
**GET** `/writer/payouts/`

Response example:
```json
[
  {
    "id": "uuid",
    "amount": "2500.00",
    "status": "processed",
    "reference_id": "UPI-TXN-987654",
    "period_start": "2025-06-01",
    "period_end": "2025-06-30",
    "processed_at": "2025-07-02T10:00:00Z"
  }
]
```

---

## NOTIFICATIONS

### My Notifications
**GET** `/notifications/`
Returns last 50 notifications for the logged-in writer.

---

### Mark Notification as Read
**POST** `/notifications/<notification_id>/read/`
Body: `{}`

---

## LOGOUT

### Logout
**POST** `/auth/logout/`
```json
{ "refresh": "<refresh_token>" }
```
