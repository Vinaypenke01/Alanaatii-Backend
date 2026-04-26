# Alanaatii API Documentation Index

**Base URL:** `http://localhost:8000/api/v1`
**Swagger UI:** `http://localhost:8000/api/docs/`

---

## Role-Based API Reference

| File | Role | Auth | Endpoints |
|------|------|------|-----------|
| [API_PUBLIC.md](./API_PUBLIC.md) | Anyone (No login) | None | Register, Login, Browse Catalog, Place Order, FAQ, Reviews |
| [API_CUSTOMER.md](./API_CUSTOMER.md) | Customer (`user`) | Bearer user token | Profile, Addresses, My Orders, Questionnaire, Script Actions |
| [API_WRITER.md](./API_WRITER.md) | Writer (`writer`) | Bearer writer token | Assignments, Draft, Submit Script, Payouts, Stats |
| [API_ADMIN.md](./API_ADMIN.md) | Admin (`admin`) | Bearer admin token | Orders, Payments, Refunds, Writers, Catalog, Settings, Coupons |

---

## Postman Quick Setup

1. Create a new **Environment** in Postman with these variables:

| Variable | Value |
|----------|-------|
| `base_url` | `http://localhost:8000/api/v1` |
| `admin_token` | *(paste from admin login)* |
| `user_token` | *(paste from user login)* |
| `writer_token` | *(paste from writer login)* |

2. Use `{{base_url}}` in all URLs and `Bearer {{admin_token}}` as the Authorization header.

---

## End-to-End Test Flow (15 steps)

```
1.  POST /auth/admin/login/              → get admin_token
2.  PUT  /admin/settings/               → set UPI ID
3.  POST /admin/catalog/                → add letter_theme item  (save uuid → A)
4.  POST /admin/catalog/                → add text_style item    (save uuid → B)
5.  POST /admin/questions/              → add questions for "Lover" relation
6.  POST /auth/user/register/           → get user_token
7.  POST /orders/                       → place order (use A, B)  (save order_id → O)
8.  GET  /admin/payments/?status=pending → find transaction_id   (save → T)
9.  POST /admin/payments/T/verify/      → verify payment
10. POST /orders/O/questionnaire/       → submit answers (as customer)
11. GET  /writer/assignments/?status=pending → find assignment_id (save → AS)
12. POST /writer/assignments/AS/accept/ → writer accepts
13. POST /writer/orders/O/submit-script/ → writer submits script
14. POST /orders/O/script-action/       → customer approves script
15. PATCH /admin/orders/O/status/       → set delivered
```
