# Alanaatii Backend — Setup & Run Guide

## Prerequisites
- Python 3.11+
- pip

---

## 1. Create & Activate Virtual Environment

```bash
cd e:\Client-Projects\alanaatii\Full_stack\Alanaatii-Backend

python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Environment Variables
The `.env` file is pre-configured with:
- Railway PostgreSQL URL
- Gmail SMTP credentials
- CORS for localhost:5173

No changes needed for development.

## 4. Run Django System Check

```bash
python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

## 5. Run Migrations

```bash
python manage.py migrate
```

## 6. Create First Admin Account

```bash
python manage.py shell
```

Then in the shell:
```python
from apps.accounts.models import Admin
admin = Admin()
admin.full_name = 'Super Admin'
admin.email = 'admin@alanaatii.com'
admin.role = 'super_admin'
admin.is_active = True
admin.is_staff = True
admin.set_password('Admin@1234')
admin.save()
print('Admin created!')
exit()
```

## 7. Start Development Server

```bash
python manage.py runserver 8000
```

## 8. API Documentation

Visit: http://localhost:8000/api/docs/

---

## API Overview

### Auth Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/v1/auth/user/register/` | Customer registration |
| POST | `/api/v1/auth/user/login/` | Customer login |
| POST | `/api/v1/auth/writer/login/` | Writer login |
| POST | `/api/v1/auth/admin/login/` | Admin login |
| POST | `/api/v1/auth/token/refresh/` | Refresh JWT |

### Public Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/catalog/?category=paper` | Browse catalog |
| GET | `/api/v1/relations/` | Relation categories |
| GET | `/api/v1/settings/` | UPI & support info |
| GET | `/api/v1/questions/?relation_type=Mother` | Questionnaire |
| POST | `/api/v1/coupons/validate/` | Validate coupon |
| POST | `/api/v1/orders/` | Place order (guest OK) |
| GET | `/api/v1/reviews/` | Published reviews |
| POST | `/api/v1/reviews/submit/` | Submit review |
| GET | `/api/v1/faq/` | FAQ |
| POST | `/api/v1/support/` | Contact form |

### Customer Dashboard (JWT required)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/orders/my/` | My orders |
| GET | `/api/v1/orders/<id>/` | Order detail |
| POST | `/api/v1/orders/<id>/questionnaire/` | Submit answers |
| POST | `/api/v1/orders/<id>/script-action/` | Approve/revise |
| POST | `/api/v1/orders/<id>/cancel/` | Cancel order |
| GET/PUT | `/api/v1/user/profile/` | Profile |
| GET/POST | `/api/v1/user/addresses/` | Saved addresses |
| GET | `/api/v1/notifications/` | Notifications |

### Writer Portal (JWT required)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/writer/assignments/` | My assignments |
| POST | `/api/v1/writer/assignments/<id>/accept/` | Accept |
| POST | `/api/v1/writer/assignments/<id>/decline/` | Decline |
| GET | `/api/v1/writer/orders/` | Assigned orders |
| POST | `/api/v1/writer/orders/<id>/submit-script/` | Submit script |
| GET/PUT | `/api/v1/writer/orders/<id>/draft/` | Auto-save draft |
| GET | `/api/v1/writer/payouts/` | My payouts |
| GET | `/api/v1/writer/stats/` | Statistics |

### Admin Panel (JWT required)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/admin/orders/` | All orders (filterable) |
| PATCH | `/api/v1/admin/orders/<id>/status/` | Update status |
| POST | `/api/v1/admin/orders/<id>/reassign/` | Reassign writer |
| GET | `/api/v1/admin/payments/` | Pending payments |
| POST | `/api/v1/admin/payments/<id>/verify/` | Verify payment |
| POST | `/api/v1/admin/payments/<id>/reject/` | Reject payment |
| GET | `/api/v1/admin/analytics/` | Dashboard analytics |
| GET/POST | `/api/v1/admin/writers/` | Writer management |
| GET/POST | `/api/v1/admin/catalog/` | Catalog management |
| GET/PUT | `/api/v1/admin/settings/` | Site settings |
| GET/POST | `/api/v1/admin/coupons/` | Coupon management |
| GET/POST | `/api/v1/admin/payouts/` | Payout management |
| GET | `/api/v1/admin/refunds/` | Refunds |
| GET | `/api/v1/admin/support/` | Support messages |
| GET | `/api/v1/admin/audit-logs/` | Audit trail |

---

## JWT Usage

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

Token payload contains `role` field: `user`, `writer`, or `admin`.
