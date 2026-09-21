"""backend_test_e12.py — E12 (Import Session) + E11 (Tiers/Bulk/Settings) API Testing

Tests E12 session-based import endpoints and E11 features before RELEASE.
"""
import os
import sys
import httpx
from typing import Dict, Any, List

# Use public endpoint from frontend/.env
BASE_URL = "https://multi-admin-io.preview.emergentagent.com/api"
ADMIN_CREDS = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
CUSTOMER_CREDS = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}

class E12Tester:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=60)
        self.admin_token = None
        self.customer_token = None
        self.admin_headers = {}
        self.customer_headers = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.session_ids = []
        
    def test(self, name: str, condition: bool, details: str = ""):
        """Run a test and track results"""
        self.tests_run += 1
        status = "✓" if condition else "✗"
        if condition:
            self.tests_passed += 1
            print(f"{status} {name}")
        else:
            print(f"{status} {name} — FAILED: {details}")
        return condition
    
    def login_admin(self):
        """Login as admin"""
        print("\n=== ADMIN AUTHENTICATION ===")
        try:
            r = self.client.post("/auth/login", json=ADMIN_CREDS)
            if r.status_code == 200:
                data = r.json()
                self.admin_token = data.get("token")
                self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
                return self.test("Admin login successful", bool(self.admin_token))
            else:
                return self.test("Admin login successful", False, f"Status {r.status_code}")
        except Exception as e:
            return self.test("Admin login successful", False, str(e))
    
    def login_customer(self):
        """Login as customer"""
        print("\n=== CUSTOMER AUTHENTICATION ===")
        try:
            r = self.client.post("/auth/login", json=CUSTOMER_CREDS)
            if r.status_code == 200:
                data = r.json()
                self.customer_token = data.get("token")
                self.customer_headers = {"Authorization": f"Bearer {self.customer_token}"}
                return self.test("Customer login successful", bool(self.customer_token))
            else:
                return self.test("Customer login successful", False, f"Status {r.status_code}")
        except Exception as e:
            return self.test("Customer login successful", False, str(e))
    
    def test_e12_analyze_session(self):
        """Test POST /api/admin/products/io/analyze with session creation"""
        print("\n=== E12: POST /analyze (Session Creation) ===")
        try:
            # Read small test file
            file_path = "/app/tests/import_samples/qa_tier_small.csv"
            with open(file_path, "rb") as f:
                files = {"file": ("qa_tier_small.csv", f, "text/csv")}
                r = self.client.post(
                    "/admin/products/io/analyze?include_rows=false&preview=200",
                    files=files,
                    headers=self.admin_headers
                )
            
            if not self.test("POST /analyze returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            session_id = data.get("session_id")
            self.session_ids.append(session_id)
            
            self.test("Response has session_id", bool(session_id))
            self.test("Response has headers", isinstance(data.get("headers"), list))
            self.test("Response has suggested_mapping", isinstance(data.get("suggested_mapping"), dict))
            self.test("Response has total", isinstance(data.get("total"), int))
            self.test("Response has expires_at", bool(data.get("expires_at")))
            
            # Verify include_rows=false means no 'rows' in response (only preview_rows)
            self.test("include_rows=false -> no 'rows' field", "rows" not in data)
            self.test("preview_rows present", isinstance(data.get("preview_rows"), list))
            
            # Verify response is small (KB not MB)
            response_size = len(r.text)
            self.test("Response size < 500KB", response_size < 500000, f"Size: {response_size} bytes")
            
            return True
        except Exception as e:
            self.test("POST /analyze works", False, str(e))
            return False
    
    def test_e12_validate_session(self):
        """Test POST /api/admin/products/io/validate with session_id"""
        print("\n=== E12: POST /validate (Session-based) ===")
        if not self.session_ids:
            print("Skipping - no session created")
            return False
        
        try:
            session_id = self.session_ids[0]
            payload = {
                "session_id": session_id,
                "mapping": {
                    "name": "name",
                    "category": "category",
                    "variant_price": "variant_price"
                },
                "report_limit": 200,
                "product_limit": 100
            }
            
            r = self.client.post("/admin/products/io/validate", json=payload, headers=self.admin_headers)
            
            if not self.test("POST /validate returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            summary = data.get("summary", {})
            
            self.test("Response has summary", bool(summary))
            self.test("Summary has rows/ok/error/products", 
                     all(k in summary for k in ["rows", "ok", "error", "products"]))
            
            # Verify limited response (not full reports/products)
            self.test("Response has reports_head (limited)", isinstance(data.get("reports_head"), list))
            self.test("Response has products_head (limited)", isinstance(data.get("products_head"), list))
            self.test("Response has error_reports", isinstance(data.get("error_reports"), list))
            self.test("No full 'reports' array", "reports" not in data or data.get("reports") == [])
            self.test("No full 'products' array", "products" not in data or data.get("products") == [])
            
            # Verify response is small
            response_size = len(r.text)
            self.test("Response size < 500KB", response_size < 500000, f"Size: {response_size} bytes")
            
            return True
        except Exception as e:
            self.test("POST /validate works", False, str(e))
            return False
    
    def test_e12_tiers_session(self):
        """Test POST /api/admin/products/io/tiers with session_id"""
        print("\n=== E12: POST /tiers (Session-based) ===")
        if not self.session_ids:
            print("Skipping - no session created")
            return False
        
        try:
            session_id = self.session_ids[0]
            payload = {
                "session_id": session_id,
                "mapping": {
                    "name": "name",
                    "category": "category",
                    "tags": "tags"
                },
                "tier_column": "tags"
            }
            
            r = self.client.post("/admin/products/io/tiers", json=payload, headers=self.admin_headers)
            
            if not self.test("POST /tiers returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            
            self.test("Response has tier_column", bool(data.get("tier_column")))
            self.test("Response has tiers", isinstance(data.get("tiers"), list))
            self.test("Response has dimensions", isinstance(data.get("dimensions"), list))
            self.test("Response has combos", isinstance(data.get("combos"), list))
            self.test("Response has cell_rows", isinstance(data.get("cell_rows"), dict))
            self.test("Response has summary", isinstance(data.get("summary"), dict))
            
            return True
        except Exception as e:
            self.test("POST /tiers works", False, str(e))
            return False
    
    def test_e12_session_rows(self):
        """Test GET /api/admin/products/io/session/{sid}/rows"""
        print("\n=== E12: GET /session/{sid}/rows ===")
        if not self.session_ids:
            print("Skipping - no session created")
            return False
        
        try:
            session_id = self.session_ids[0]
            r = self.client.get(
                f"/admin/products/io/session/{session_id}/rows?offset=0&limit=100",
                headers=self.admin_headers
            )
            
            if not self.test("GET /session/{sid}/rows returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            
            self.test("Response has session_id", data.get("session_id") == session_id)
            self.test("Response has total", isinstance(data.get("total"), int))
            self.test("Response has headers", isinstance(data.get("headers"), list))
            self.test("Response has rows", isinstance(data.get("rows"), list))
            
            return True
        except Exception as e:
            self.test("GET /session/{sid}/rows works", False, str(e))
            return False
    
    def test_e12_session_cells(self):
        """Test POST /api/admin/products/io/session/{sid}/cells"""
        print("\n=== E12: POST /session/{sid}/cells ===")
        if not self.session_ids:
            print("Skipping - no session created")
            return False
        
        try:
            session_id = self.session_ids[0]
            payload = {
                "cells": [
                    {"row": 0, "header": "variant_price", "value": "999999"}
                ]
            }
            
            r = self.client.post(
                f"/admin/products/io/session/{session_id}/cells",
                json=payload,
                headers=self.admin_headers
            )
            
            if not self.test("POST /session/{sid}/cells returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            
            self.test("Response has session_id", data.get("session_id") == session_id)
            self.test("Response has updated count", isinstance(data.get("updated"), int))
            self.test("Response has total", isinstance(data.get("total"), int))
            
            return True
        except Exception as e:
            self.test("POST /session/{sid}/cells works", False, str(e))
            return False
    
    def test_e12_session_fill(self):
        """Test POST /api/admin/products/io/session/{sid}/fill"""
        print("\n=== E12: POST /session/{sid}/fill ===")
        if not self.session_ids:
            print("Skipping - no session created")
            return False
        
        try:
            session_id = self.session_ids[0]
            payload = {
                "mapping": {
                    "name": "name",
                    "category": "category",
                    "tags": "tags"
                },
                "tier_column": "tags",
                "dim_order": ["Ukuran", "Tipe"],
                "matrix_price": {
                    "CP01": {"35ml|Standard": 150000, "60ml|Standard": 250000},
                    "CP02": {"35ml|Standard": 200000, "60ml|Standard": 300000}
                },
                "matrix_compare": {},
                "overwrite_price": False,
                "stock": "0",
                "status": "archived",
                "concentration": "file"
            }
            
            r = self.client.post(
                f"/admin/products/io/session/{session_id}/fill",
                json=payload,
                headers=self.admin_headers
            )
            
            if not self.test("POST /session/{sid}/fill returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            
            self.test("Response has session_id", data.get("session_id") == session_id)
            self.test("Response has stats", isinstance(data.get("stats"), dict))
            self.test("Response has total", isinstance(data.get("total"), int))
            
            return True
        except Exception as e:
            self.test("POST /session/{sid}/fill works", False, str(e))
            return False
    
    def test_e12_session_close(self):
        """Test POST /api/admin/products/io/session/{sid}/close"""
        print("\n=== E12: POST /session/{sid}/close ===")
        if not self.session_ids:
            print("Skipping - no session created")
            return False
        
        try:
            session_id = self.session_ids[0]
            r = self.client.post(
                f"/admin/products/io/session/{session_id}/close",
                headers=self.admin_headers
            )
            
            if not self.test("POST /session/{sid}/close returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            self.test("Response has closed=True", data.get("closed") == True)
            
            # Verify session is now inaccessible (404)
            r2 = self.client.get(
                f"/admin/products/io/session/{session_id}/rows",
                headers=self.admin_headers
            )
            self.test("Closed session returns 404", r2.status_code == 404)
            
            return True
        except Exception as e:
            self.test("POST /session/{sid}/close works", False, str(e))
            return False
    
    def test_e12_pruning(self):
        """Test E12 pruning: create 7 sessions, verify only <=5 remain"""
        print("\n=== E12: Session Pruning (MAX_PER_ADMIN=5) ===")
        try:
            created_sessions = []
            file_path = "/app/tests/import_samples/qa_tier_small.csv"
            
            # Create 7 sessions
            for i in range(7):
                with open(file_path, "rb") as f:
                    files = {"file": (f"test_{i}.csv", f, "text/csv")}
                    r = self.client.post(
                        "/admin/products/io/analyze?include_rows=false&preview=10",
                        files=files,
                        headers=self.admin_headers
                    )
                
                if r.status_code == 200:
                    session_id = r.json().get("session_id")
                    created_sessions.append(session_id)
            
            self.test("Created 7 sessions", len(created_sessions) == 7)
            
            # Verify oldest sessions are pruned (first 2 should be gone)
            oldest_session = created_sessions[0]
            newest_session = created_sessions[-1]
            
            # Try to access oldest session (should be 404)
            r_old = self.client.get(
                f"/admin/products/io/session/{oldest_session}/rows",
                headers=self.admin_headers
            )
            self.test("Oldest session pruned (404)", r_old.status_code == 404, f"Status: {r_old.status_code}")
            
            # Try to access newest session (should work)
            r_new = self.client.get(
                f"/admin/products/io/session/{newest_session}/rows",
                headers=self.admin_headers
            )
            self.test("Newest session still accessible (200)", r_new.status_code == 200, f"Status: {r_new.status_code}")
            
            # Clean up remaining sessions
            for sid in created_sessions[-5:]:
                try:
                    self.client.post(f"/admin/products/io/session/{sid}/close", headers=self.admin_headers)
                except Exception:
                    pass
            
            return True
        except Exception as e:
            self.test("Session pruning works", False, str(e))
            return False
    
    def test_e12_rbac(self):
        """Test RBAC: 401 without token, 403 as customer, 404 for invalid session"""
        print("\n=== E12: RBAC & Owner-Scope ===")
        try:
            # Test 401 without token
            r = self.client.post("/admin/products/io/analyze")
            self.test("No token -> 401", r.status_code == 401, f"Status: {r.status_code}")
            
            # Test 403 as customer
            file_path = "/app/tests/import_samples/qa_tier_small.csv"
            with open(file_path, "rb") as f:
                files = {"file": ("test.csv", f, "text/csv")}
                r = self.client.post(
                    "/admin/products/io/analyze",
                    files=files,
                    headers=self.customer_headers
                )
            self.test("Customer -> 403", r.status_code == 403, f"Status: {r.status_code}")
            
            # Test 404 for invalid session_id
            r = self.client.get(
                "/admin/products/io/session/invalid_session_id/rows",
                headers=self.admin_headers
            )
            self.test("Invalid session_id -> 404", r.status_code == 404, f"Status: {r.status_code}")
            
            # Test 422 for bad payload (cells not list)
            if self.session_ids:
                r = self.client.post(
                    f"/admin/products/io/session/{self.session_ids[0]}/cells",
                    json={"cells": "not_a_list"},
                    headers=self.admin_headers
                )
                self.test("Bad cells payload -> 422", r.status_code == 422, f"Status: {r.status_code}")
            
            return True
        except Exception as e:
            self.test("RBAC tests work", False, str(e))
            return False
    
    def test_e11_bulk_status(self):
        """Test POST /api/admin/products/bulk-status"""
        print("\n=== E11: POST /bulk-status ===")
        try:
            # Get some product IDs
            r = self.client.get("/products", headers=self.admin_headers)
            products = r.json()
            if not products:
                print("No products to test bulk-status")
                return False
            
            product_ids = [p["id"] for p in products[:3]]
            
            # Test archive
            payload = {
                "ids": product_ids,
                "status": "archived",
                "confirm_count": len(product_ids)
            }
            
            r = self.client.post("/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            
            if not self.test("POST /bulk-status returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            self.test("Response has matched", isinstance(data.get("matched"), int))
            self.test("Response has modified", isinstance(data.get("modified"), int))
            
            # Test activate back
            payload["status"] = "active"
            r = self.client.post("/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            self.test("Activate back returns 200", r.status_code == 200)
            
            # Test confirm_count mismatch -> 409
            payload["confirm_count"] = 999
            r = self.client.post("/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            self.test("Confirm_count mismatch -> 409", r.status_code == 409, f"Status: {r.status_code}")
            
            # Test invalid status -> 422
            payload["confirm_count"] = len(product_ids)
            payload["status"] = "invalid_status"
            r = self.client.post("/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            self.test("Invalid status -> 422", r.status_code == 422, f"Status: {r.status_code}")
            
            return True
        except Exception as e:
            self.test("POST /bulk-status works", False, str(e))
            return False
    
    def test_e11_settings(self):
        """Test GET/PUT /api/settings and /api/admin/settings"""
        print("\n=== E11: Settings (inspired_by) ===")
        try:
            # Test GET /api/settings (public)
            r = self.client.get("/settings")
            if not self.test("GET /settings returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            settings = r.json()
            self.test("Settings has inspired_by_enabled", "inspired_by_enabled" in settings)
            self.test("Settings has inspired_by_label", "inspired_by_label" in settings)
            self.test("Settings has house_brands", "house_brands" in settings)
            
            original_settings = settings.copy()
            
            # Test PUT /api/admin/settings
            new_settings = {
                "inspired_by_enabled": False,
                "inspired_by_label": "Test Label",
                "house_brands": ["Test Brand", "Another Brand"]
            }
            
            r = self.client.put("/admin/settings", json=new_settings, headers=self.admin_headers)
            if not self.test("PUT /admin/settings returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            # Verify changes
            r = self.client.get("/settings")
            updated = r.json()
            self.test("inspired_by_enabled updated", updated.get("inspired_by_enabled") == False)
            self.test("inspired_by_label updated", updated.get("inspired_by_label") == "Test Label")
            
            # Restore original settings
            restore = {
                "inspired_by_enabled": True,
                "inspired_by_label": "Inspired by",
                "house_brands": ["Collector Parfum", "Collector"]
            }
            r = self.client.put("/admin/settings", json=restore, headers=self.admin_headers)
            self.test("Settings restored", r.status_code == 200)
            
            return True
        except Exception as e:
            self.test("Settings endpoints work", False, str(e))
            return False
    
    def test_regression_smoke(self):
        """Smoke test regression endpoints"""
        print("\n=== REGRESSION: Smoke Tests ===")
        try:
            endpoints = [
                ("/health", None),
                ("/products", None),
                ("/categories", None),
                ("/admin/dashboard", self.admin_headers),
                ("/admin/products", self.admin_headers),
                ("/admin/orders", self.admin_headers),
            ]
            
            all_ok = True
            for path, headers in endpoints:
                r = self.client.get(path, headers=headers)
                ok = self.test(f"GET {path} returns 200", r.status_code == 200, f"Status: {r.status_code}")
                if not ok:
                    all_ok = False
            
            return all_ok
        except Exception as e:
            self.test("Regression smoke tests work", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all E12/E11 tests"""
        print("=" * 70)
        print("E12 (IMPORT SESSION) + E11 (TIERS/BULK/SETTINGS) API TESTS")
        print("=" * 70)
        
        # Authentication
        if not self.login_admin():
            print("\n❌ Cannot proceed without admin authentication")
            return False
        
        if not self.login_customer():
            print("\n⚠️  Customer login failed, skipping customer RBAC tests")
        
        # E12 Session Tests
        self.test_e12_analyze_session()
        self.test_e12_validate_session()
        self.test_e12_tiers_session()
        self.test_e12_session_rows()
        self.test_e12_session_cells()
        self.test_e12_session_fill()
        self.test_e12_session_close()
        
        # E12 Pruning (NEW CODE)
        self.test_e12_pruning()
        
        # E12 RBAC
        self.test_e12_rbac()
        
        # E11 Features
        self.test_e11_bulk_status()
        self.test_e11_settings()
        
        # Regression
        self.test_regression_smoke()
        
        # Summary
        print("\n" + "=" * 70)
        print(f"RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 70)
        
        if self.tests_passed == self.tests_run:
            print("✓ All E12/E11 backend tests passed!")
            return True
        else:
            print(f"✗ {self.tests_run - self.tests_passed} test(s) failed")
            return False

def main():
    tester = E12Tester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
