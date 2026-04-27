# Alanaatii API Documentation Index

**Base URL:** `http://localhost:8000/api/v1`
**Swagger UI:** `http://localhost:8000/api/docs/`

---

## Role-Based API Reference

| File | Role | Auth | Endpoints |
|------|------|------|-----------|
| [API_PUBLIC.md](./API_PUBLIC.md) | Anyone (No login) | None | Register/Login (password or Google OAuth), Browse Catalog, Place Order, FAQ, Reviews |
| [API_CUSTOMER.md](./API_CUSTOMER.md) | Customer (`user`) | Bearer user token | Profile, Addresses, My Orders, Questionnaire, Script Actions |
| [API_WRITER.md](./API_WRITER.md) | Writer (`writer`) | Bearer writer token | Assignments, Draft, Submit Script, Payouts, Stats |
| [API_ADMIN.md](./API_ADMIN.md) | Admin (`admin`) | Bearer admin token | Orders, Payments, Refunds, Writers, Catalog, Settings, Coupons |

---

## Auth Mode Configuration

Controlled by `AUTH_MODE_PASSWORD` in your `.env` file.

| Setting | Customer Login Method |
|---|---|
| `AUTH_MODE_PASSWORD=True` | ✅ Email + Password `POST /auth/user/register/` and `POST /auth/user/login/` |
| `AUTH_MODE_PASSWORD=False` | ✅ Google OAuth `POST /auth/user/google/` (1-click, no password needed) |

> **Note:** Writer and Admin logins are always password-based regardless of this setting.
> When `AUTH_MODE_PASSWORD=False`, you must also set `GOOGLE_CLIENT_ID` in `.env`.

---

## Postman Quick Setup

1. Create a new **Environment** in Postman with these variables:

| Variable | Value |
|----------|-------|
| `base_url` | `http://localhost:8000/api/v1` |
| `admin_token` | *(paste from admin login)* |
| `user_token` | *(paste from user/google login)* |
| `writer_token` | *(paste from writer login)* |

2. Use `{{base_url}}` in all URLs and `Bearer {{admin_token}}` as the Authorization header.

---

## End-to-End Test Flow (15 steps)

```
1.  POST /auth/admin/login/               → get admin_token
2.  PUT  /admin/settings/                 → set UPI ID, enable auto_assign_writers
3.  POST /admin/catalog/                  → add letter_theme item  (save uuid → A)
4.  POST /admin/catalog/                  → add text_style item    (save uuid → B)
5.  POST /admin/questions/                → add questions for a relation type
6.  POST /auth/user/register/             → get user_token        [password mode]
    OR
    POST /auth/user/google/               → get user_token        [OAuth mode]
7.  POST /orders/                         → place order (use A, B)  (save order_id → O)
8.  GET  /admin/payments/?status=pending  → find transaction_id   (save → T)
9.  POST /admin/payments/T/verify/        → verify payment
10. POST /orders/O/questionnaire/         → submit answers (as customer)
11. GET  /writer/assignments/?status=pending → find assignment_id (save → AS)
12. POST /writer/assignments/AS/accept/   → writer accepts
13. POST /writer/orders/O/submit-script/  → writer submits script
14. POST /orders/O/script-action/         → customer approves script
15. PATCH /admin/orders/O/status/         → set delivered
```

---

## New APIs Added (April 2026)

| Endpoint | Method | Description |
|---|---|---|
| `/auth/user/google/` | `POST` | Google OAuth login/register for customers |
| `/admin/settings/` | `PUT` | Update site settings including `auto_assign_writers` |

### Auth Mode Guards
When the wrong auth mode is used, the API returns a helpful `403` response pointing to the correct endpoint.

---

## Total API Count: 79 endpoints across 7 apps
