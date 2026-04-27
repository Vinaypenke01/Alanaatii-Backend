import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
REPORT_DATA = []

def run_test(name, method, url, auth_token=None, data=None):
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"Testing: {name}...")
    try:
        url_full = f"{BASE_URL}{url}"
        if method == "GET":
            res = requests.get(url_full, headers=headers)
        elif method == "POST":
            res = requests.post(url_full, headers=headers, json=data)
        elif method == "PUT":
            res = requests.put(url_full, headers=headers, json=data)
        elif method == "PATCH":
            res = requests.patch(url_full, headers=headers, json=data)
        elif method == "DELETE":
            res = requests.delete(url_full, headers=headers)
        
        passed = res.status_code in [200, 201, 204]
        
        try:
            resp_data = res.json()
        except:
            resp_data = res.text

        REPORT_DATA.append({
            "name": name,
            "method": method,
            "url": url,
            "status_code": res.status_code,
            "passed": passed,
            "response": resp_data
        })
        
        if not passed:
            print(f"  ❌ Failed with {res.status_code}: {resp_data}")
        else:
            print(f"  ✅ Passed ({res.status_code})")
            
        return passed, resp_data
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        REPORT_DATA.append({
            "name": name,
            "method": method,
            "url": url,
            "status_code": "ERROR",
            "passed": False,
            "response": str(e)
        })
        return False, {}

def main():
    print("========================================")
    print("🚀 Starting Alanaatii E2E API Flow Test")
    print("========================================\n")
    
    timestamp = int(time.time())
    cust_email = f"customer_{timestamp}@example.com"
    writer_email = f"writer_{timestamp}@example.com"
    coupon_code = f"TEST{timestamp}"
    relation_name = f"FlowTest_{timestamp}"

    # 1. Admin Login
    passed, res = run_test("Admin Login", "POST", "/auth/admin/login/", data={
        "email": "admin@alanaatii.com",
        "password": "Admin@1234"
    })
    if not passed: 
        print("\n❌ Admin login failed. Ensure the server is running and admin exists.")
        return
    admin_token = res['tokens']['access']

    # 1.5 Enable Auto-Assign via Settings
    run_test("Update Site Settings", "PUT", "/admin/settings/", auth_token=admin_token, data={
        "master_upi_id": "test@upi",
        "support_email": "support@test.com",
        "support_whatsapp": "9999999999",
        "maintenance_mode": False,
        "auto_assign_writers": True,
        "default_delivery_fee": "50.00"
    })

    # 2. Add Catalog Items
    passed, res = run_test("Add Letter Theme", "POST", "/admin/catalog/", auth_token=admin_token, data={
        "category": "letter_theme", "title": f"Vintage Theme {timestamp}", "price": "100.00", "is_active": True
    })
    theme_id = res.get('id') if isinstance(res, dict) else None

    passed, res = run_test("Add Text Style", "POST", "/admin/catalog/", auth_token=admin_token, data={
        "category": "style", "title": f"Cursive {timestamp}", "price": "50.00", "is_active": True
    })
    style_id = res.get('id') if isinstance(res, dict) else None

    # 3. Add Relation & Questions
    run_test("Add Relation", "POST", "/admin/relations/", auth_token=admin_token, data={
        "name": relation_name, "is_active": True
    })
    
    passed, res = run_test("Add Question", "POST", "/admin/questions/", auth_token=admin_token, data={
        "relation_type": relation_name, "question_text": "How did you meet?", "display_order": 1, "is_required": True
    })
    question_id = res.get('id', 1) if isinstance(res, dict) else 1

    # 4. Add Coupon
    run_test("Add Coupon", "POST", "/admin/coupons/", auth_token=admin_token, data={
        "code": coupon_code, "discount_val": "10.00", "discount_type": "percentage", 
        "max_uses": 100, "valid_from": "2025-01-01", "valid_until": "2026-12-31", 
        "min_order": "0.00", "is_active": True
    })

    # 5. Create Writer
    run_test("Create Writer", "POST", "/admin/writers/", auth_token=admin_token, data={
        "full_name": "Test Writer", "email": writer_email, "phone": str(timestamp)[:10], 
        "phone_alt": "", "address": "Writer City", "languages": ["English"], "password": "Writer@123"
    })

    # 6. Customer Register & Login
    run_test("Customer Register", "POST", "/auth/user/register/", data={
        "full_name": "Test Customer", "email": cust_email, "phone_wa": str(timestamp)[:10], 
        "password": "Customer@123", "password_confirm": "Customer@123"
    })
    
    passed, res = run_test("Customer Login", "POST", "/auth/user/login/", data={
        "email": cust_email, "password": "Customer@123"
    })
    if not passed: return
    user_token = res['tokens']['access']

    # 7. Place Order
    order_payload = {
        "product_type": "letter",
        "customer_name": "Test Customer",
        "customer_phone": str(timestamp)[:10],
        "customer_email": cust_email,
        "recipient_name": "Test Recipient",
        "recipient_phone": "6666666666",
        "primary_contact": "sender",
        "relation": relation_name,
        "address": "123 Test St",
        "city": "Test City",
        "pincode": "500000",
        "delivery_date": "2025-06-15",
        "coupon_code": coupon_code
    }
    if theme_id: order_payload["letter_theme"] = theme_id
    if style_id: order_payload["text_style"] = style_id

    passed, res = run_test("Place Order", "POST", "/orders/", auth_token=user_token, data=order_payload)
    if not passed: return
    order_id = res['order']['id']

    # 8. Admin Verify Payment
    passed, res = run_test("Get Pending Payments", "GET", "/admin/payments/?status=pending", auth_token=admin_token)
    txn_id = None
    txn_list = res.get('results', []) if isinstance(res, dict) else res
    if passed and isinstance(txn_list, list):
        for txn in txn_list:
            if txn.get('order', {}).get('id') == order_id:
                txn_id = txn['id']
                break
    
    if txn_id:
        run_test("Verify Payment", "POST", f"/admin/payments/{txn_id}/verify/", auth_token=admin_token, data={})
    else:
        print("  ❌ Could not find pending transaction for order.")

    # 9. Submit Questionnaire
    run_test("Submit Questionnaire", "POST", f"/orders/{order_id}/questionnaire/", auth_token=user_token, data={
        "answers": [{"question_id": question_id, "answer": "At school"}]
    })

    # 10. Writer Login
    passed, res = run_test("Writer Login", "POST", "/auth/writer/login/", data={
        "email": writer_email, "password": "Writer@123"
    })
    if not passed: return
    writer_token = res['tokens']['access']

    # 11. Writer Get Assignments & Accept
    passed, res = run_test("Get Writer Assignments", "GET", "/writer/assignments/?status=pending", auth_token=writer_token)
    assignment_id = None
    assignment_list = res.get('results', []) if isinstance(res, dict) else res
    if passed and isinstance(assignment_list, list) and len(assignment_list) > 0:
        assignment_id = assignment_list[0]['id']
    
    if assignment_id:
        run_test("Accept Assignment", "POST", f"/writer/assignments/{assignment_id}/accept/", auth_token=writer_token, data={})
    else:
        print("  ⚠️ Could not find assignment for writer (Auto-assign might be disabled or delayed).")

    # 12. Writer Submit Script
    run_test("Submit Script", "POST", f"/writer/orders/{order_id}/submit-script/", auth_token=writer_token, data={
        "content": "This is the final test script.",
        "writer_note": "Enjoy!"
    })

    # 13. Customer Approve Script
    run_test("Approve Script", "POST", f"/orders/{order_id}/script-action/", auth_token=user_token, data={
        "action": "approve"
    })

    # 14. Admin Mark Delivered
    run_test("Mark Delivered", "PATCH", f"/admin/orders/{order_id}/status/", auth_token=admin_token, data={
        "new_status": "delivered",
        "note": "Test flow complete"
    })

    # Generate Markdown Report
    print("\n========================================")
    print("📄 Generating Detailed Report...")
    print("========================================")
    
    report_md = "# 🧪 Alanaatii End-to-End API Test Report\n\n"
    report_md += "> This report was generated automatically by the E2E test script to validate the entire order lifecycle.\n\n"
    report_md += "| Step | Action | Method | Path | Status |\n"
    report_md += "|---|---|---|---|---|\n"
    
    for i, row in enumerate(REPORT_DATA, 1):
        icon = "✅" if row['passed'] else "❌"
        report_md += f"| {i} | {row['name']} | `{row['method']}` | `{row['url']}` | {icon} `{row['status_code']}` |\n"
    
    report_md += "\n## 🚨 Detailed Failures\n"
    has_failures = False
    for row in REPORT_DATA:
        if not row['passed']:
            has_failures = True
            report_md += f"### ❌ {row['name']} (`{row['url']}`)\n"
            report_md += f"**Status Code:** `{row['status_code']}`\n"
            report_md += "**Response:**\n```json\n"
            try:
                report_md += json.dumps(row['response'], indent=2)
            except:
                report_md += str(row['response'])
            report_md += "\n```\n\n"
    
    if not has_failures:
        report_md += "> **All endpoints passed successfully! The API architecture is solid.** 🎉\n"

    with open("docs/TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_md)
    print("✅ Report successfully saved to: docs/TEST_REPORT.md\n")

if __name__ == "__main__":
    main()
