"""
Alanaatii API — Production Traffic / Load Test
Target: https://alanaatii-backend-production.up.railway.app

Uses: Locust (pip install locust)

─── Quick Start ─────────────────────────────────────────────────────────────
# 1. Headless run — 50 users, ramp 5/sec, run 2 minutes, save HTML report
locust -f locustfile.py \
    --host=https://alanaatii-backend-production.up.railway.app \
    --headless -u 50 -r 5 --run-time 2m \
    --html=docs/TRAFFIC_REPORT.html

# 2. Interactive Web UI — open http://localhost:8089 and configure from browser
locust -f locustfile.py \
    --host=https://alanaatii-backend-production.up.railway.app

# 3. Stress test — gradually ramp to 200 users
locust -f locustfile.py \
    --host=https://alanaatii-backend-production.up.railway.app \
    --headless -u 200 -r 10 --run-time 5m \
    --html=docs/STRESS_REPORT.html
─────────────────────────────────────────────────────────────────────────────

APIs Tested (by user role):
┌─────────────────┬──────┬──────────────────────────────────────────────────────────────────┐
│ Role            │  %   │ Endpoints covered                                                │
├─────────────────┼──────┼──────────────────────────────────────────────────────────────────┤
│ BrowseUser      │  55% │ /catalog/, /questions/, /settings/, /faq/,                   │
│ (anonymous)     │      │ /reviews/, /site-steps/, /coupons/validate/                      │
├─────────────────┼──────┼──────────────────────────────────────────────────────────────────┤
│ CustomerUser    │  25% │ register, login, /orders/, /orders/my/, /orders/<id>/,           │
│ (authenticated) │      │ /orders/<id>/questionnaire/, /orders/<id>/cancel/,               │
│                 │      │ /orders/<id>/script-action/, /user/profile/,                     │
│                 │      │ /user/addresses/, /notifications/                                │
├─────────────────┼──────┼──────────────────────────────────────────────────────────────────┤
│ AdminUser       │  12% │ /admin/orders/, /admin/payments/, /admin/analytics/,             │
│ (authenticated) │      │ /admin/writers/, /admin/catalog/, /admin/coupons/,               │
│                 │      │ /admin/settings/, /admin/support/, /admin/refunds/,              │
│                 │      │ /admin/audit-logs/, /admin/payouts/                              │
├─────────────────┼──────┼──────────────────────────────────────────────────────────────────┤
│ WriterUser      │   8% │ /writer/assignments/, /writer/orders/, /writer/stats/,           │
│ (authenticated) │      │ /writer/payouts/, /writer/orders/<id>/draft/                    │
└─────────────────┴──────┴──────────────────────────────────────────────────────────────────┘
"""

import json
import random
import time
from locust import HttpUser, task, between, events

# ─── CONFIGURE THESE BEFORE RUNNING ─────────────────────────────────────────

# Admin credentials (must already exist in Railway DB)
ADMIN_CREDS = {
    "email": "admin@alanaatii.com",
    "password": "Admin@1234"
}

# Writer credentials (must already exist in Railway DB — created by admin)
# Replace with real writer credentials from your DB
WRITER_CREDS = {
    "email": "ngbeam706@gmail.com",
    "password": "12345678"
}

# ─── Static test data ────────────────────────────────────────────────────────

RELATION_TYPES = ["Lover / Partner", "Mother", "Father", "Friend", "Sibling"]
CATALOG_CATEGORIES = ["letter_theme", "style", "paper", "box", "gift", "package"]
DELIVERY_DATES = ["2026-08-15", "2026-09-01", "2026-10-20", "2026-12-25"]
PINCODE_SAMPLES = ["500001", "560001", "400001", "110001", "600001"]


# ─── Shared login helper ─────────────────────────────────────────────────────

def get_token(client, url, payload, label="[AUTH] Login"):
    """Login and return access token, or None on failure."""
    with client.post(url, json=payload, catch_response=True, name=label) as res:
        if res.status_code == 200:
            data = res.json()
            return data.get("tokens", {}).get("access")
        res.failure(f"Login failed: {res.status_code} — {res.text[:200]}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ANONYMOUS BROWSER — 55% traffic
#    Tests: Public endpoints that any visitor hits
# ═══════════════════════════════════════════════════════════════════════════════

class BrowseUser(HttpUser):
    """
    Simulates an anonymous visitor browsing the Alanaatii store.
    These are READ-ONLY, no-auth endpoints — the most frequent real-world traffic.
    """
    weight = 55
    wait_time = between(1, 4)

    @task(6)
    def browse_catalog(self):
        """GET all catalog items — heaviest read endpoint."""
        self.client.get("/api/v1/catalog/", name="[PUBLIC] GET /catalog/")

    @task(5)
    def browse_catalog_by_category(self):
        """GET catalog filtered by category — simulates frontend dropdown selection."""
        cat = random.choice(CATALOG_CATEGORIES)
        self.client.get(f"/api/v1/catalog/?category={cat}", name="[PUBLIC] GET /catalog/?category")

    @task(4)
    def get_questions(self):
        """GET questionnaire questions — called when customer picks a relation."""
        relation = random.choice(RELATION_TYPES)
        self.client.get(f"/api/v1/questions/?relation_type={relation}", name="[PUBLIC] GET /questions/")

    @task(3)
    def get_faq(self):
        """GET FAQ page content."""
        self.client.get("/api/v1/faq/", name="[PUBLIC] GET /faq/")

    @task(3)
    def get_reviews(self):
        """GET published customer reviews."""
        self.client.get("/api/v1/reviews/", name="[PUBLIC] GET /reviews/")

    @task(2)
    def get_site_steps(self):
        """GET how-it-works steps for homepage."""
        self.client.get("/api/v1/site-steps/", name="[PUBLIC] GET /site-steps/")

    @task(2)
    def get_settings(self):
        """GET UPI ID and support info — shown on payment page."""
        self.client.get("/api/v1/settings/", name="[PUBLIC] GET /settings/")

    @task(2)
    def validate_coupon(self):
        """POST coupon validation — happens frequently during checkout."""
        coupon_codes = ["TEST60",]
        self.client.post(
            "/api/v1/coupons/validate/",
            json={
                "code": random.choice(coupon_codes),
                "order_total": round(random.uniform(500, 5000), 2)
            },
            name="[PUBLIC] POST /coupons/validate/"
        )

    @task(1)
    def submit_review(self):
        """POST a public review — occasional action after delivery."""
        self.client.post(
            "/api/v1/reviews/submit/",
            json={
                "customer_name": f"Tester {random.randint(1, 999)}",
                "rating": random.randint(4, 5),
                "content": "Beautiful letter! Loved it."
            },
            name="[PUBLIC] POST /reviews/submit/"
        )

    @task(1)
    def submit_support(self):
        """POST contact form — low frequency."""
        self.client.post(
            "/api/v1/support/",
            json={
                "name": "Test User",
                "email": f"test{random.randint(1, 9999)}@example.com",
                "phone": "9876543210",
                "message": "I need help with my order."
            },
            name="[PUBLIC] POST /support/"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CUSTOMER (LOGGED IN) — 25% traffic
#    Tests: Full order journey — register → login → order → questionnaire → review
# ═══════════════════════════════════════════════════════════════════════════════

class CustomerUser(HttpUser):
    """
    Simulates a logged-in customer going through the order lifecycle.
    Each virtual user registers a fresh account on startup.
    """
    weight = 25
    wait_time = between(2, 6)

    token = None
    order_id = None

    def on_start(self):
        """Register a new customer and capture the JWT token."""
        ts = int(time.time() * 1000)
        rnd = random.randint(100, 9999)
        email = f"loadtest_{ts}_{rnd}@traffic.test"
        payload = {
            "full_name": "Load Tester",
            "email": email,
            "phone_wa": "9" + str(random.randint(100000000, 999999999)),
            "password": "Test@12345",
            "password_confirm": "Test@12345"
        }
        with self.client.post(
            "/api/v1/auth/user/register/",
            json=payload,
            catch_response=True,
            name="[CUSTOMER] POST /auth/user/register/"
        ) as res:
            if res.status_code == 201:
                self.token = res.json().get("tokens", {}).get("access")
            elif res.status_code == 403:
                # AUTH_MODE_PASSWORD=False on server → try login flow
                self.token = get_token(
                    self.client,
                    "/api/v1/auth/user/login/",
                    {"email": email, "password": "Test@12345"},
                    label="[CUSTOMER] POST /auth/user/login/"
                )
            else:
                res.failure(f"Register failed: {res.status_code} — {res.text[:300]}")

    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def view_my_orders(self):
        """GET customer's own order list — most frequent customer action."""
        if not self.token:
            return
        self.client.get("/api/v1/orders/my/", headers=self._auth(), name="[CUSTOMER] GET /orders/my/")

    @task(4)
    def view_profile(self):
        """GET user profile."""
        if not self.token:
            return
        self.client.get("/api/v1/user/profile/", headers=self._auth(), name="[CUSTOMER] GET /user/profile/")

    @task(3)
    def view_notifications(self):
        """GET in-app notifications."""
        if not self.token:
            return
        self.client.get("/api/v1/notifications/", headers=self._auth(), name="[CUSTOMER] GET /notifications/")

    @task(3)
    def place_order(self):
        """POST a new order — triggers pricing engine + email + DB writes."""
        if not self.token:
            return
        product = random.choice(["letter", "letterBox", "letterBoxGift", "script", "letterPaper"])
        payload = {
            "product_type": product,
            "customer_name": "Load Tester",
            "customer_country_code": "+91",
            "customer_phone": "9876543210",
            "customer_email": "loadtest@traffic.test",
            "recipient_name": "Test Recipient",
            "recipient_country_code": "+91",
            "recipient_phone": "9000000000",
            "primary_contact": "sender",
            "relation": random.choice(RELATION_TYPES),
            "address": "123 Test Street, MG Road",
            "city": "Hyderabad",
            "pincode": random.choice(PINCODE_SAMPLES),
            "delivery_date": random.choice(DELIVERY_DATES),
            "express_script": False,
            "paper_quantity": 1,
        }
        with self.client.post(
            "/api/v1/orders/",
            json=payload,
            headers=self._auth(),
            catch_response=True,
            name="[CUSTOMER] POST /orders/"
        ) as res:
            if res.status_code == 201:
                self.order_id = res.json().get("order", {}).get("id")
            elif res.status_code in [400, 422]:
                res.success()  # validation errors are expected
            else:
                res.failure(f"Place order failed: {res.status_code} — {res.text[:200]}")

    @task(2)
    def view_order_detail(self):
        """GET a specific order — triggered when customer clicks order in list."""
        if not self.token or not self.order_id:
            return
        self.client.get(
            f"/api/v1/orders/{self.order_id}/",
            headers=self._auth(),
            name="[CUSTOMER] GET /orders/<id>/"
        )

    @task(2)
    def submit_questionnaire(self):
        """POST questionnaire answers — required after payment verification."""
        if not self.token or not self.order_id:
            return
        self.client.post(
            f"/api/v1/orders/{self.order_id}/questionnaire/",
            json={
                "answers": [
                    {"question_id": 1, "answer": "We met at college"},
                    {"question_id": 2, "answer": "She loves poetry and sunsets"},
                    {"question_id": 3, "answer": "Our first trip to Goa"},
                ]
            },
            headers=self._auth(),
            name="[CUSTOMER] POST /orders/<id>/questionnaire/"
        )

    @task(1)
    def view_addresses(self):
        """GET saved addresses list."""
        if not self.token:
            return
        self.client.get("/api/v1/user/addresses/", headers=self._auth(), name="[CUSTOMER] GET /user/addresses/")

    @task(1)
    def approve_script(self):
        """POST script approval — customer approves the written script."""
        if not self.token or not self.order_id:
            return
        self.client.post(
            f"/api/v1/orders/{self.order_id}/script-action/",
            json={"action": "approve"},
            headers=self._auth(),
            name="[CUSTOMER] POST /orders/<id>/script-action/ (approve)"
        )

    @task(1)
    def request_revision(self):
        """POST revision request — customer asks for changes."""
        if not self.token or not self.order_id:
            return
        self.client.post(
            f"/api/v1/orders/{self.order_id}/script-action/",
            json={"action": "revise", "feedback": "Please make it more emotional and personal."},
            headers=self._auth(),
            name="[CUSTOMER] POST /orders/<id>/script-action/ (revise)"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ADMIN USER — 12% traffic
#    Tests: Admin dashboard operations — orders, payments, analytics, management
# ═══════════════════════════════════════════════════════════════════════════════

class AdminUser(HttpUser):
    """
    Simulates an admin managing daily operations.
    Uses real admin credentials — must exist in Railway DB.
    """
    weight = 12
    wait_time = between(3, 10)

    token = None

    def on_start(self):
        self.token = get_token(
            self.client,
            "/api/v1/auth/admin/login/",
            ADMIN_CREDS,
            label="[ADMIN] POST /auth/admin/login/"
        )

    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(6)
    def list_orders_filtered(self):
        """GET all orders with status filter — admin's most used page."""
        if not self.token:
            return
        status = random.choice([
            "payment_pending", "awaiting_details", "order_placed",
            "assigned_to_writer", "accepted_by_writer", "customer_review",
            "out_for_delivery", "delivered"
        ])
        self.client.get(
            f"/api/v1/admin/orders/?status={status}",
            headers=self._auth(),
            name="[ADMIN] GET /admin/orders/?status"
        )

    @task(5)
    def list_pending_payments(self):
        """GET pending payment verifications — high priority daily task."""
        if not self.token:
            return
        self.client.get(
            "/api/v1/admin/payments/?status=pending",
            headers=self._auth(),
            name="[ADMIN] GET /admin/payments/?status=pending"
        )

    @task(4)
    def get_analytics(self):
        """GET dashboard analytics — revenue, counts, charts."""
        if not self.token:
            return
        self.client.get(
            "/api/v1/admin/analytics/",
            headers=self._auth(),
            name="[ADMIN] GET /admin/analytics/"
        )

    @task(3)
    def list_writers(self):
        """GET all writers with optional status filter."""
        if not self.token:
            return
        status = random.choice(["active", "inactive", ""])
        url = "/api/v1/admin/writers/" + (f"?status={status}" if status else "")
        self.client.get(url, headers=self._auth(), name="[ADMIN] GET /admin/writers/")

    @task(2)
    def list_catalog_admin(self):
        """GET full catalog as admin (includes inactive items)."""
        if not self.token:
            return
        self.client.get("/api/v1/admin/catalog/", headers=self._auth(), name="[ADMIN] GET /admin/catalog/")

    @task(2)
    def list_coupons(self):
        """GET all coupons."""
        if not self.token:
            return
        self.client.get("/api/v1/admin/coupons/", headers=self._auth(), name="[ADMIN] GET /admin/coupons/")

    @task(2)
    def list_support_messages(self):
        """GET support/contact messages."""
        if not self.token:
            return
        self.client.get("/api/v1/admin/support/", headers=self._auth(), name="[ADMIN] GET /admin/support/")

    @task(2)
    def get_audit_logs(self):
        """GET audit trail — admin oversight."""
        if not self.token:
            return
        self.client.get("/api/v1/admin/audit-logs/", headers=self._auth(), name="[ADMIN] GET /admin/audit-logs/")

    @task(1)
    def list_refunds(self):
        """GET refund requests."""
        if not self.token:
            return
        self.client.get("/api/v1/admin/refunds/", headers=self._auth(), name="[ADMIN] GET /admin/refunds/")

    @task(1)
    def list_payouts(self):
        """GET writer payout records."""
        if not self.token:
            return
        self.client.get("/api/v1/admin/payouts/", headers=self._auth(), name="[ADMIN] GET /admin/payouts/")

    @task(1)
    def get_site_settings_admin(self):
        """GET current site settings (UPI, delivery fee, etc.)."""
        if not self.token:
            return
        self.client.get("/api/v1/admin/settings/", headers=self._auth(), name="[ADMIN] GET /admin/settings/")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. WRITER USER — 8% traffic
#    Tests: Writer portal — assignments, script drafts, stats, payouts
# ═══════════════════════════════════════════════════════════════════════════════

class WriterUser(HttpUser):
    """
    Simulates a writer managing their assignments.
    Uses real writer credentials — must exist in Railway DB (created by admin).
    Set WRITER_CREDS at top of this file before running.
    """
    weight = 8
    wait_time = between(5, 15)

    token = None
    assignment_id = None
    order_id = None

    def on_start(self):
        self.token = get_token(
            self.client,
            "/api/v1/auth/writer/login/",
            WRITER_CREDS,
            label="[WRITER] POST /auth/writer/login/"
        )

    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(6)
    def get_pending_assignments(self):
        """GET pending assignments — first thing writer checks on login."""
        if not self.token:
            return
        with self.client.get(
            "/api/v1/writer/assignments/?status=pending",
            headers=self._auth(),
            catch_response=True,
            name="[WRITER] GET /writer/assignments/?status=pending"
        ) as res:
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", []) if isinstance(data, dict) else data
                if results:
                    self.assignment_id = results[0].get("id")
                    self.order_id = results[0].get("order")

    @task(4)
    def get_accepted_assignments(self):
        """GET accepted/active assignments."""
        if not self.token:
            return
        self.client.get(
            "/api/v1/writer/assignments/?status=accepted",
            headers=self._auth(),
            name="[WRITER] GET /writer/assignments/?status=accepted"
        )

    @task(4)
    def get_writer_orders(self):
        """GET all orders assigned to this writer."""
        if not self.token:
            return
        self.client.get("/api/v1/writer/orders/", headers=self._auth(), name="[WRITER] GET /writer/orders/")

    @task(3)
    def get_writer_stats(self):
        """GET writer statistics — completed jobs, earnings, etc."""
        if not self.token:
            return
        self.client.get("/api/v1/writer/stats/", headers=self._auth(), name="[WRITER] GET /writer/stats/")

    @task(2)
    def get_writer_payouts(self):
        """GET writer's payout history."""
        if not self.token:
            return
        self.client.get("/api/v1/writer/payouts/", headers=self._auth(), name="[WRITER] GET /writer/payouts/")

    @task(2)
    def autosave_draft(self):
        """PUT auto-save draft — called frequently as writer types."""
        if not self.token or not self.order_id:
            return
        self.client.put(
            f"/api/v1/writer/orders/{self.order_id}/draft/",
            json={"draft_content": "Dear beloved,\n\nI wanted to write to you about..."},
            headers=self._auth(),
            name="[WRITER] PUT /writer/orders/<id>/draft/"
        )

    @task(1)
    def get_draft(self):
        """GET saved draft for an order."""
        if not self.token or not self.order_id:
            return
        self.client.get(
            f"/api/v1/writer/orders/{self.order_id}/draft/",
            headers=self._auth(),
            name="[WRITER] GET /writer/orders/<id>/draft/"
        )

    @task(1)
    def accept_assignment(self):
        """POST accept an assignment."""
        if not self.token or not self.assignment_id:
            return
        self.client.post(
            f"/api/v1/writer/assignments/{self.assignment_id}/accept/",
            json={},
            headers=self._auth(),
            name="[WRITER] POST /writer/assignments/<id>/accept/"
        )

    @task(1)
    def get_writer_profile(self):
        """GET writer's own profile."""
        if not self.token:
            return
        self.client.get("/api/v1/writer/profile/", headers=self._auth(), name="[WRITER] GET /writer/profile/")
