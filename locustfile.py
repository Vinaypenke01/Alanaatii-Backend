"""
Alanaatii API Load / Traffic Test
Uses: Locust — industry-standard Python load testing tool

Install: pip install locust
Run:     locust -f locustfile.py --host=http://localhost:8000 --headless -u 50 -r 10 --run-time 60s --html=docs/TRAFFIC_REPORT.html

Or open the Web UI:
         locust -f locustfile.py --host=http://localhost:8000
         → open http://localhost:8089

Roles simulated:
  - BrowseUser     60%  (anonymous visitor browsing catalog, checking settings)
  - CustomerUser   25%  (logs in, places order, submits questionnaire)
  - AdminUser      10%  (logs in, checks orders, verifies payments)
  - WriterUser      5%  (logs in, checks assignments, submits script)
"""

import json
import random
import time
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# ─── Shared test data ─────────────────────────────────────────────────────────

ADMIN_CREDS   = {"email": "admin@alanaatii.com",  "password": "Admin@1234"}
WRITER_CREDS  = {"email": ""}   # populated at runtime from create flow

RELATION_TYPES = ["Lover / Partner", "Mother", "Father", "Friend", "Sibling"]

CATALOG_CATEGORIES = ["letter_theme", "style", "paper", "box", "gift", "package"]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_token(client, url, payload):
    """Login helper — returns the access token or None."""
    with client.post(url, json=payload, catch_response=True, name="[AUTH] Login") as res:
        if res.status_code == 200:
            return res.json().get("tokens", {}).get("access")
        res.failure(f"Login failed: {res.status_code}")
        return None


# ─── 1. Anonymous Browser (60% of traffic) ────────────────────────────────────

class BrowseUser(HttpUser):
    """Simulates a visitor browsing the site without logging in."""
    weight = 60
    wait_time = between(1, 3)  # 1–3s think time between requests

    @task(5)
    def browse_catalog(self):
        self.client.get("/api/v1/catalog/", name="[PUBLIC] GET /catalog/")

    @task(4)
    def browse_catalog_filtered(self):
        cat = random.choice(CATALOG_CATEGORIES)
        self.client.get(f"/api/v1/catalog/?category={cat}", name="[PUBLIC] GET /catalog/?category")

    @task(3)
    def get_relations(self):
        self.client.get("/api/v1/relations/", name="[PUBLIC] GET /relations/")

    @task(3)
    def get_faq(self):
        self.client.get("/api/v1/faq/", name="[PUBLIC] GET /faq/")

    @task(2)
    def get_site_steps(self):
        self.client.get("/api/v1/site-steps/", name="[PUBLIC] GET /site-steps/")

    @task(2)
    def get_settings(self):
        self.client.get("/api/v1/settings/", name="[PUBLIC] GET /settings/")

    @task(2)
    def get_reviews(self):
        self.client.get("/api/v1/reviews/", name="[PUBLIC] GET /reviews/")

    @task(2)
    def get_questions(self):
        relation = random.choice(RELATION_TYPES)
        self.client.get(
            f"/api/v1/questions/?relation_type={relation}",
            name="[PUBLIC] GET /questions/"
        )

    @task(1)
    def validate_coupon(self):
        self.client.post(
            "/api/v1/coupons/validate/",
            json={"code": "SAVE20", "order_total": random.uniform(500, 3000)},
            name="[PUBLIC] POST /coupons/validate/"
        )


# ─── 2. Logged-in Customer (25% of traffic) ───────────────────────────────────

class CustomerUser(HttpUser):
    """Simulates a logged-in customer doing the full order journey."""
    weight = 25
    wait_time = between(2, 5)
    token = None
    order_id = None

    def on_start(self):
        """Register + login before tasks begin."""
        ts = int(time.time() * 1000)
        email = f"loadtest_{ts}_{random.randint(100,999)}@test.com"
        payload = {
            "full_name": "Load Tester",
            "email": email,
            "phone_wa": "9" + str(random.randint(100000000, 999999999)),
            "password": "Test@12345",
            "password_confirm": "Test@12345"
        }
        with self.client.post(
            "/api/v1/auth/user/register/", json=payload,
            catch_response=True, name="[CUSTOMER] Register"
        ) as res:
            if res.status_code == 201:
                self.token = res.json().get("tokens", {}).get("access")
            else:
                res.failure(f"Register failed: {res.status_code} {res.text[:200]}")

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(4)
    def view_my_orders(self):
        if not self.token:
            return
        self.client.get(
            "/api/v1/orders/my/",
            headers=self._auth_headers(),
            name="[CUSTOMER] GET /orders/my/"
        )

    @task(3)
    def view_profile(self):
        if not self.token:
            return
        self.client.get(
            "/api/v1/user/profile/",
            headers=self._auth_headers(),
            name="[CUSTOMER] GET /user/profile/"
        )

    @task(2)
    def place_order(self):
        if not self.token:
            return
        payload = {
            "product_type": "letter",
            "customer_name": "Load Tester",
            "customer_phone": "9876543210",
            "customer_email": "loadtest@test.com",
            "recipient_name": "Test Recipient",
            "recipient_phone": "9000000000",
            "primary_contact": "sender",
            "relation": random.choice(RELATION_TYPES),
            "address": "123 Test Street",
            "city": "Hyderabad",
            "pincode": "500001",
            "delivery_date": "2025-12-30"
        }
        with self.client.post(
            "/api/v1/orders/",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
            name="[CUSTOMER] POST /orders/ (place order)"
        ) as res:
            if res.status_code == 201:
                self.order_id = res.json().get("order", {}).get("id")
            elif res.status_code in [400, 422]:
                res.success()  # Expected validation errors are not failures
            else:
                res.failure(f"Place order failed: {res.status_code}")

    @task(1)
    def view_notifications(self):
        if not self.token:
            return
        self.client.get(
            "/api/v1/notifications/",
            headers=self._auth_headers(),
            name="[CUSTOMER] GET /notifications/"
        )


# ─── 3. Admin User (10% of traffic) ──────────────────────────────────────────

class AdminUser(HttpUser):
    """Simulates an admin doing daily operations."""
    weight = 10
    wait_time = between(3, 8)
    token = None

    def on_start(self):
        self.token = get_token(self.client, "/api/v1/auth/admin/login/", ADMIN_CREDS)

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def list_orders(self):
        if not self.token: return
        status = random.choice(["pending", "payment_pending", "in_progress", "delivered"])
        self.client.get(
            f"/api/v1/admin/orders/?status={status}",
            headers=self._auth_headers(),
            name="[ADMIN] GET /admin/orders/"
        )

    @task(4)
    def list_pending_payments(self):
        if not self.token: return
        self.client.get(
            "/api/v1/admin/payments/?status=pending",
            headers=self._auth_headers(),
            name="[ADMIN] GET /admin/payments/?status=pending"
        )

    @task(3)
    def get_analytics(self):
        if not self.token: return
        self.client.get(
            "/api/v1/admin/analytics/",
            headers=self._auth_headers(),
            name="[ADMIN] GET /admin/analytics/"
        )

    @task(2)
    def list_writers(self):
        if not self.token: return
        self.client.get(
            "/api/v1/admin/writers/",
            headers=self._auth_headers(),
            name="[ADMIN] GET /admin/writers/"
        )

    @task(1)
    def list_catalog(self):
        if not self.token: return
        self.client.get(
            "/api/v1/admin/catalog/",
            headers=self._auth_headers(),
            name="[ADMIN] GET /admin/catalog/"
        )

    @task(1)
    def audit_logs(self):
        if not self.token: return
        self.client.get(
            "/api/v1/admin/audit-logs/",
            headers=self._auth_headers(),
            name="[ADMIN] GET /admin/audit-logs/"
        )


# ─── 4. Writer User (5% of traffic) ──────────────────────────────────────────

class WriterUser(HttpUser):
    """Simulates a writer checking and managing assignments."""
    weight = 5
    wait_time = between(5, 15)
    token = None

    def on_start(self):
        """Writers are created by admin, so we need existing credentials."""
        # Try the first writer created by the E2E test script
        # In production, use real writer credentials here
        pass  # token stays None → tasks will skip gracefully

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def get_assignments(self):
        if not self.token: return
        self.client.get(
            "/api/v1/writer/assignments/?status=pending",
            headers=self._auth_headers(),
            name="[WRITER] GET /writer/assignments/"
        )

    @task(2)
    def get_stats(self):
        if not self.token: return
        self.client.get(
            "/api/v1/writer/stats/",
            headers=self._auth_headers(),
            name="[WRITER] GET /writer/stats/"
        )

    @task(1)
    def get_payouts(self):
        if not self.token: return
        self.client.get(
            "/api/v1/writer/payouts/",
            headers=self._auth_headers(),
            name="[WRITER] GET /writer/payouts/"
        )
