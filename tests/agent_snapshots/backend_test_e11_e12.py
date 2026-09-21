"""backend_test_e11_e12.py — Comprehensive API testing for E11 & E12 features.

Tests E12 (Import Session):
1. POST /api/admin/products/io/analyze (session_id + preview_rows)
2. POST /api/admin/products/io/validate (session_id vs rows compatibility)
3. POST /api/admin/products/io/tiers (session_id + cell_rows)
4. GET /api/admin/products/io/session/{sid}/rows (offset/limit/indexes)
5. POST /api/admin/products/io/session/{sid}/cells (patch edit)
6. POST /api/admin/products/io/session/{sid}/fill (bulk fill matrix)
7. POST /api/admin/products/io/session/{sid}/close
8. Deviant cases (401, 403, 404, 422)

Tests E11 (Bulk Actions + Settings):
1. POST /api/admin/products/bulk-status (ids + filter)
2. GET /api/settings (inspired_by settings)
3. PUT /api/admin/settings
"""
import os
import sys
import httpx
from typing import Dict, Any, Optional

# Use environment variable for base URL
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://parfum-bulk-feature.preview.emergentagent.com").rstrip("/")
ADMIN_CREDS = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
CUSTOMER_CREDS = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}

# Test files
FILE_TESTIMPORT = "/app/tests/user_uploads/testimport.xlsx"  # 6426 rows, price=1000, ALL VALID
FILE_PRICE_ZERO = "/app/tests/user_uploads/IMPOR_PRODUK_COLLECTOR_PARFUM_1.xlsx"  # 6426 rows, price=0
FILE_SMALL = "/app/tests/import_samples/qa_tier_small.csv"  # 3 products, small file


class APITester:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=120)  # Long timeout for large files
        self.admin_token = None
        self.customer_token = None
        self.admin_headers = {}
        self.customer_headers = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None
        self.original_settings = None
        
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
        """Login as admin and get token"""
        print("\n=== AUTHENTICATION (ADMIN) ===")
        try:
            r = self.client.post("/api/auth/login", json=ADMIN_CREDS)
            if r.status_code == 200:
                data = r.json()
                self.admin_token = data.get("token")
                self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
                return self.test("Admin login successful", bool(self.admin_token))
            else:
                return self.test("Admin login successful", False, f"Status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            return self.test("Admin login successful", False, str(e))
    
    def login_customer(self):
        """Login as customer and get token"""
        print("\n=== AUTHENTICATION (CUSTOMER) ===")
        try:
            r = self.client.post("/api/auth/login", json=CUSTOMER_CREDS)
            if r.status_code == 200:
                data = r.json()
                self.customer_token = data.get("token")
                self.customer_headers = {"Authorization": f"Bearer {self.customer_token}"}
                return self.test("Customer login successful", bool(self.customer_token))
            else:
                return self.test("Customer login successful", False, f"Status {r.status_code}")
        except Exception as e:
            return self.test("Customer login successful", False, str(e))
    
    # ========== E12 TESTS: IMPORT SESSION ==========
    
    def test_analyze_with_session(self):
        """E12: POST /api/admin/products/io/analyze with include_rows=false"""
        print("\n=== E12 TEST: POST /analyze (session_id + preview) ===")
        try:
            with open(FILE_TESTIMPORT, "rb") as f:
                files = {"file": ("testimport.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                r = self.client.post(
                    "/api/admin/products/io/analyze?include_rows=false&preview=200",
                    files=files,
                    headers=self.admin_headers
                )
            
            if not self.test("POST /analyze returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            self.session_id = data.get("session_id")
            
            self.test("Response has session_id", bool(self.session_id) and self.session_id.startswith("imp_"))
            self.test("Response has total=6426", data.get("total") == 6426, f"Got {data.get('total')}")
            self.test("Response has preview_rows (200 items)", len(data.get("preview_rows", [])) == 200)
            self.test("Response does NOT have 'rows' key", "rows" not in data, "Should not include full rows")
            self.test("Response size < 400 KB", len(r.text) < 400000, f"Size: {len(r.text)} bytes")
            
            return True
        except Exception as e:
            self.test("POST /analyze works", False, str(e))
            return False
    
    def test_validate_with_session(self):
        """E12: POST /api/admin/products/io/validate with session_id"""
        print("\n=== E12 TEST: POST /validate (session_id) ===")
        if not self.session_id:
            print("Skipping - no session_id")
            return False
        
        try:
            # Use suggested mapping from analyze
            payload = {
                "session_id": self.session_id,
                "mapping": {
                    "slug": "slug",
                    "name": "name",
                    "brand": "brand",
                    "category": "category",
                    "concentration": "concentration",
                    "gender": "gender",
                    "description": "description",
                    "tags": "tags",
                    "occasions": "occasions",
                    "characters": "characters",
                    "status": "status",
                    "option1_name": "option1_name",
                    "option1_value": "option1_value",
                    "option2_name": "option2_name",
                    "option2_value": "option2_value",
                    "variant_price": "variant_price",
                    "variant_stock": "variant_stock",
                    "variant_sku": "variant_sku"
                },
                "report_limit": 200,
                "product_limit": 20
            }
            
            r = self.client.post("/api/admin/products/io/validate", json=payload, headers=self.admin_headers)
            
            if not self.test("POST /validate returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            summary = data.get("summary", {})
            
            self.test("Summary rows=6426", summary.get("rows") == 6426, f"Got {summary.get('rows')}")
            self.test("Summary ok=6426", summary.get("ok") == 6426, f"Got {summary.get('ok')}")
            self.test("Summary error=0", summary.get("error") == 0, f"Got {summary.get('error')}")
            self.test("Summary products=1071", summary.get("products") == 1071, f"Got {summary.get('products')}")
            
            self.test("Response has reports_head (200 items)", len(data.get("reports_head", [])) == 200)
            self.test("Response has products_head (20 items)", len(data.get("products_head", [])) == 20)
            self.test("Response has reports_total=6426", data.get("reports_total") == 6426)
            self.test("Response has products_total=1071", data.get("products_total") == 1071)
            self.test("Response does NOT have full 'reports' array", "reports" not in data or len(data.get("reports", [])) < 6426)
            self.test("Response size < 500 KB", len(r.text) < 500000, f"Size: {len(r.text)} bytes")
            
            return True
        except Exception as e:
            self.test("POST /validate with session_id works", False, str(e))
            return False
    
    def test_tiers_with_session(self):
        """E12+E11: POST /api/admin/products/io/tiers with session_id"""
        print("\n=== E12+E11 TEST: POST /tiers (session_id + cell_rows) ===")
        if not self.session_id:
            print("Skipping - no session_id")
            return False
        
        try:
            payload = {
                "session_id": self.session_id,
                "mapping": {
                    "slug": "slug",
                    "name": "name",
                    "brand": "brand",
                    "category": "category",
                    "concentration": "concentration",
                    "gender": "gender",
                    "description": "description",
                    "tags": "tags",
                    "occasions": "occasions",
                    "characters": "characters",
                    "status": "status",
                    "option1_name": "option1_name",
                    "option1_value": "option1_value",
                    "option2_name": "option2_name",
                    "option2_value": "option2_value",
                    "variant_price": "variant_price",
                    "variant_stock": "variant_stock",
                    "variant_sku": "variant_sku"
                }
            }
            
            r = self.client.post("/api/admin/products/io/tiers", json=payload, headers=self.admin_headers)
            
            if not self.test("POST /tiers returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            
            self.test("tier_column='tags'", data.get("tier_column") == "tags")
            
            tiers = data.get("tiers", [])
            self.test("Has 4 tiers", len(tiers) == 4, f"Got {len(tiers)} tiers")
            
            # Check tier products count (use 'label' not 'tier')
            tier_products = {t["label"]: t["products"] for t in tiers}
            expected_products = {"CP01": 532, "CP02": 417, "CP03": 107, "EXCLUSIVE": 15}
            self.test("Tier products match", tier_products == expected_products, f"Got {tier_products}")
            
            # Check tier rows count
            tier_rows = {t["label"]: t["rows"] for t in tiers}
            expected_rows = {"CP01": 3192, "CP02": 2502, "CP03": 642, "EXCLUSIVE": 90}
            self.test("Tier rows match", tier_rows == expected_rows, f"Got {tier_rows}")
            
            dimensions = data.get("dimensions", [])
            self.test("Has 2 dimensions (not 4)", len(dimensions) == 2, f"Got {len(dimensions)} dimensions")
            
            if len(dimensions) == 2:
                dim_names = [d["name"] for d in dimensions]
                self.test("Dimensions are Ukuran and Tipe", set(dim_names) == {"Ukuran", "Tipe"})
            
            combos = data.get("combos", [])
            self.test("Has 6 combos", len(combos) == 6, f"Got {len(combos)} combos")
            
            summary = data.get("summary", {})
            self.test("Summary cells=24", summary.get("cells") == 24, f"Got {summary.get('cells')}")
            
            self.test("Has cell_rows field", "cell_rows" in data)
            
            return True
        except Exception as e:
            self.test("POST /tiers with session_id works", False, str(e))
            return False
    
    def test_session_rows(self):
        """E12: GET /api/admin/products/io/session/{sid}/rows"""
        print("\n=== E12 TEST: GET /session/{sid}/rows ===")
        if not self.session_id:
            print("Skipping - no session_id")
            return False
        
        try:
            # Test offset/limit
            r = self.client.get(
                f"/api/admin/products/io/session/{self.session_id}/rows?offset=0&limit=100",
                headers=self.admin_headers
            )
            
            if not self.test("GET /session/{sid}/rows returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            data = r.json()
            self.test("Returns 100 rows", len(data.get("rows", [])) == 100)
            self.test("Total=6426", data.get("total") == 6426)
            
            # Test indexes
            r = self.client.get(
                f"/api/admin/products/io/session/{self.session_id}/rows?indexes=0,5,6425",
                headers=self.admin_headers
            )
            
            if r.status_code == 200:
                data = r.json()
                rows = data.get("rows", [])
                self.test("Returns exactly 3 rows for indexes=0,5,6425", len(rows) == 3)
                if len(rows) == 3:
                    indexes = [row.get("index") for row in rows]
                    self.test("Indexes are correct", indexes == [0, 5, 6425])
            
            return True
        except Exception as e:
            self.test("GET /session/{sid}/rows works", False, str(e))
            return False
    
    def test_session_cells(self):
        """E12: POST /api/admin/products/io/session/{sid}/cells"""
        print("\n=== E12 TEST: POST /session/{sid}/cells ===")
        if not self.session_id:
            print("Skipping - no session_id")
            return False
        
        try:
            payload = {
                "cells": [
                    {"row": 5, "header": "name", "value": "Nama Diedit QA"}
                ]
            }
            
            r = self.client.post(
                f"/api/admin/products/io/session/{self.session_id}/cells",
                json=payload,
                headers=self.admin_headers
            )
            
            if not self.test("POST /session/{sid}/cells returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            data = r.json()
            self.test("Updated=1", data.get("updated") == 1)
            
            # Verify change
            r = self.client.get(
                f"/api/admin/products/io/session/{self.session_id}/rows?indexes=5",
                headers=self.admin_headers
            )
            
            if r.status_code == 200:
                data = r.json()
                rows = data.get("rows", [])
                if rows:
                    row_data = rows[0].get("data", {})
                    self.test("Cell edit persisted", row_data.get("name") == "Nama Diedit QA")
            
            return True
        except Exception as e:
            self.test("POST /session/{sid}/cells works", False, str(e))
            return False
    
    def test_session_fill(self):
        """E12+E11: POST /api/admin/products/io/session/{sid}/fill"""
        print("\n=== E12+E11 TEST: POST /session/{sid}/fill (bulk fill matrix) ===")
        
        # Use FILE_PRICE_ZERO for this test
        try:
            with open(FILE_PRICE_ZERO, "rb") as f:
                files = {"file": ("IMPOR_PRODUK_COLLECTOR_PARFUM_1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                r = self.client.post(
                    "/api/admin/products/io/analyze?include_rows=false&preview=200",
                    files=files,
                    headers=self.admin_headers
                )
            
            if r.status_code != 200:
                self.test("POST /session/{sid}/fill setup", False, "Failed to analyze file")
                return False
            
            fill_session_id = r.json().get("session_id")
            
            # Create a 4x6 matrix (4 tiers x 6 combos = 24 cells)
            matrix_price = {
                "CP01": {
                    "35ml|Standard": 150000,
                    "35ml|Super": 160000,
                    "60ml|Standard": 250000,
                    "60ml|Super": 270000,
                    "100ml|Standard": 400000,
                    "100ml|Super": 420000
                },
                "CP02": {
                    "35ml|Standard": 180000,
                    "35ml|Super": 190000,
                    "60ml|Standard": 300000,
                    "60ml|Super": 320000,
                    "100ml|Standard": 480000,
                    "100ml|Super": 500000
                },
                "CP03": {
                    "35ml|Standard": 220000,
                    "35ml|Super": 240000,
                    "60ml|Standard": 360000,
                    "60ml|Super": 380000,
                    "100ml|Standard": 580000,
                    "100ml|Super": 600000
                },
                "EXCLUSIVE": {
                    "35ml|Standard": 300000,
                    "35ml|Super": 320000,
                    "60ml|Standard": 500000,
                    "60ml|Super": 520000,
                    "100ml|Standard": 800000,
                    "100ml|Super": 850000
                }
            }
            
            payload = {
                "mapping": {
                    "slug": "slug",
                    "name": "name",
                    "brand": "brand",
                    "category": "category",
                    "concentration": "concentration",
                    "gender": "gender",
                    "description": "description",
                    "tags": "tags",
                    "occasions": "occasions",
                    "characters": "characters",
                    "status": "status",
                    "option1_name": "option1_name",
                    "option1_value": "option1_value",
                    "option2_name": "option2_name",
                    "option2_value": "option2_value",
                    "variant_price": "variant_price",
                    "variant_stock": "variant_stock",
                    "variant_sku": "variant_sku"
                },
                "tier_column": "tags",
                "dim_order": ["Ukuran", "Tipe"],
                "matrix_price": matrix_price,
                "overwrite_price": False,
                "stock": "0",
                "status": "archived",
                "concentration": "EDP"
            }
            
            r = self.client.post(
                f"/api/admin/products/io/session/{fill_session_id}/fill",
                json=payload,
                headers=self.admin_headers
            )
            
            if not self.test("POST /session/{sid}/fill returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            stats = data.get("stats", {})
            
            self.test("Stats price_filled=6426", stats.get("price_filled") == 6426, f"Got {stats.get('price_filled')}")
            self.test("Stats rows_skipped_no_tier=0", stats.get("rows_skipped_no_tier") == 0)
            self.test("Stats rows_skipped_no_combo=0", stats.get("rows_skipped_no_combo") == 0)
            self.test("Stats rows_skipped_no_cell=0", stats.get("rows_skipped_no_cell") == 0)
            self.test("Stats forced=12852", stats.get("forced") == 12852, f"Got {stats.get('forced')}")
            
            # Validate after fill
            validate_payload = {
                "session_id": fill_session_id,
                "mapping": payload["mapping"],
                "report_limit": 200,
                "product_limit": 20
            }
            
            r = self.client.post("/api/admin/products/io/validate", json=validate_payload, headers=self.admin_headers)
            
            if r.status_code == 200:
                data = r.json()
                summary = data.get("summary", {})
                self.test("After fill: ok=6426", summary.get("ok") == 6426, f"Got {summary.get('ok')}")
                self.test("After fill: error=0", summary.get("error") == 0, f"Got {summary.get('error')}")
                self.test("After fill: products=1071", summary.get("products") == 1071, f"Got {summary.get('products')}")
                
                products_head = data.get("products_head", [])
                if products_head:
                    self.test("Product status='archived'", products_head[0].get("status") == "archived")
                    variants = products_head[0].get("variants", [])
                    if variants:
                        self.test("Variant stock=0", variants[0].get("stock") == 0)
            
            # Close session
            self.client.post(f"/api/admin/products/io/session/{fill_session_id}/close", headers=self.admin_headers)
            
            return True
        except Exception as e:
            self.test("POST /session/{sid}/fill works", False, str(e))
            return False
    
    def test_session_close(self):
        """E12: POST /api/admin/products/io/session/{sid}/close"""
        print("\n=== E12 TEST: POST /session/{sid}/close ===")
        if not self.session_id:
            print("Skipping - no session_id")
            return False
        
        try:
            r = self.client.post(
                f"/api/admin/products/io/session/{self.session_id}/close",
                headers=self.admin_headers
            )
            
            self.test("POST /session/{sid}/close returns 200", r.status_code == 200)
            
            # Verify session is closed
            r = self.client.get(
                f"/api/admin/products/io/session/{self.session_id}/rows",
                headers=self.admin_headers
            )
            
            self.test("After close: GET /rows returns 404", r.status_code == 404)
            
            return True
        except Exception as e:
            self.test("POST /session/{sid}/close works", False, str(e))
            return False
    
    def test_deviant_cases(self):
        """E12: Deviant cases (401, 403, 404, 422)"""
        print("\n=== E12 TEST: Deviant Cases ===")
        
        try:
            # 401: No token
            r = self.client.post("/api/admin/products/io/analyze")
            self.test("Analyze without token returns 401", r.status_code == 401)
            
            # 403: Customer token
            if self.customer_headers:
                with open(FILE_SMALL, "rb") as f:
                    files = {"file": ("qa_tier_small.csv", f, "text/csv")}
                    r = self.client.post(
                        "/api/admin/products/io/analyze",
                        files=files,
                        headers=self.customer_headers
                    )
                self.test("Analyze as customer returns 403", r.status_code == 403)
            
            # 404: Invalid session_id
            r = self.client.post(
                "/api/admin/products/io/validate",
                json={"session_id": "imp_tidakada", "mapping": {}},
                headers=self.admin_headers
            )
            self.test("Validate with invalid session_id returns 404", r.status_code == 404)
            
            # 422: Invalid cells format
            with open(FILE_SMALL, "rb") as f:
                files = {"file": ("qa_tier_small.csv", f, "text/csv")}
                r = self.client.post(
                    "/api/admin/products/io/analyze?include_rows=false",
                    files=files,
                    headers=self.admin_headers
                )
            
            if r.status_code == 200:
                temp_sid = r.json().get("session_id")
                r = self.client.post(
                    f"/api/admin/products/io/session/{temp_sid}/cells",
                    json={"cells": "bukan-list"},
                    headers=self.admin_headers
                )
                self.test("Cells with invalid format returns 422", r.status_code == 422)
                
                # Clean up
                self.client.post(f"/api/admin/products/io/session/{temp_sid}/close", headers=self.admin_headers)
            
            return True
        except Exception as e:
            self.test("Deviant cases work", False, str(e))
            return False
    
    # ========== E11 TESTS: BULK ACTIONS + SETTINGS ==========
    
    def test_bulk_status(self):
        """E11: POST /api/admin/products/bulk-status"""
        print("\n=== E11 TEST: POST /api/admin/products/bulk-status ===")
        
        try:
            # Get some product IDs
            r = self.client.get("/api/admin/products?limit=5", headers=self.admin_headers)
            if r.status_code != 200:
                self.test("Bulk status test", False, "Failed to get products")
                return False
            
            products = r.json()
            if len(products) < 2:
                self.test("Bulk status test", False, "Not enough products")
                return False
            
            product_ids = [p["id"] for p in products[:2]]
            
            # Archive by IDs
            payload = {
                "ids": product_ids,
                "status": "archived",
                "confirm_count": 2
            }
            
            r = self.client.post("/api/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            
            if not self.test("POST /bulk-status (by ids) returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                print(f"Response: {r.text[:500]}")
                return False
            
            data = r.json()
            self.test("Matched=2", data.get("matched") == 2, f"Got {data.get('matched')}")
            self.test("Modified=2", data.get("modified") == 2, f"Got {data.get('modified')}")
            
            # Restore them
            payload["status"] = "active"
            r = self.client.post("/api/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            self.test("Restore products returns 200", r.status_code == 200)
            
            # Test confirm_count mismatch (409)
            payload["confirm_count"] = 999
            r = self.client.post("/api/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            self.test("Confirm_count mismatch returns 409", r.status_code == 409)
            
            # Test invalid status (422/400)
            payload = {"ids": product_ids, "status": "hapus", "confirm_count": 2}
            r = self.client.post("/api/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            self.test("Invalid status returns 422/400", r.status_code in (400, 422))
            
            # Test without scope (400)
            payload = {"status": "active"}
            r = self.client.post("/api/admin/products/bulk-status", json=payload, headers=self.admin_headers)
            self.test("Without scope returns 400", r.status_code == 400)
            
            # Test without token (401)
            r = self.client.post("/api/admin/products/bulk-status", json={"ids": product_ids, "status": "active"})
            self.test("Without token returns 401", r.status_code == 401)
            
            # Test as customer (403)
            if self.customer_headers:
                r = self.client.post("/api/admin/products/bulk-status", json={"ids": product_ids, "status": "active"}, headers=self.customer_headers)
                self.test("As customer returns 403", r.status_code == 403)
            
            return True
        except Exception as e:
            self.test("POST /bulk-status works", False, str(e))
            return False
    
    def test_settings_inspired_by(self):
        """E11: GET /api/settings and PUT /api/admin/settings"""
        print("\n=== E11 TEST: Settings (inspired_by) ===")
        
        try:
            # GET public settings
            r = self.client.get("/api/settings")
            
            if not self.test("GET /api/settings returns 200", r.status_code == 200):
                return False
            
            data = r.json()
            self.original_settings = {
                "inspired_by_enabled": data.get("inspired_by_enabled"),
                "inspired_by_label": data.get("inspired_by_label"),
                "house_brands": data.get("house_brands")
            }
            
            self.test("Has inspired_by_enabled", "inspired_by_enabled" in data)
            self.test("Has inspired_by_label", "inspired_by_label" in data)
            self.test("Has house_brands", "house_brands" in data)
            
            self.test("inspired_by_enabled=true", data.get("inspired_by_enabled") == True)
            self.test("inspired_by_label='Inspired by'", data.get("inspired_by_label") == "Inspired by")
            
            house_brands = data.get("house_brands", [])
            self.test("house_brands contains 'Collector Parfum'", "Collector Parfum" in house_brands)
            self.test("house_brands contains 'Collector'", "Collector" in house_brands)
            
            # PUT admin settings
            new_settings = {
                "inspired_by_enabled": False,
                "inspired_by_label": "Terinspirasi dari",
                "house_brands": ["Collector Parfum", "Collector", "Test Brand"]
            }
            
            r = self.client.put("/api/admin/settings", json=new_settings, headers=self.admin_headers)
            
            if not self.test("PUT /api/admin/settings returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            # Verify changes
            r = self.client.get("/api/settings")
            if r.status_code == 200:
                data = r.json()
                self.test("Settings updated: inspired_by_enabled=false", data.get("inspired_by_enabled") == False)
                self.test("Settings updated: inspired_by_label changed", data.get("inspired_by_label") == "Terinspirasi dari")
                self.test("Settings updated: house_brands has 3 items", len(data.get("house_brands", [])) == 3)
            
            # Test PUT without token (401)
            r = self.client.put("/api/admin/settings", json=new_settings)
            self.test("PUT /admin/settings without token returns 401", r.status_code == 401)
            
            # Test PUT as customer (403)
            if self.customer_headers:
                r = self.client.put("/api/admin/settings", json=new_settings, headers=self.customer_headers)
                self.test("PUT /admin/settings as customer returns 403", r.status_code == 403)
            
            # RESTORE original settings
            if self.original_settings:
                r = self.client.put("/api/admin/settings", json=self.original_settings, headers=self.admin_headers)
                self.test("Settings restored to original", r.status_code == 200)
            
            return True
        except Exception as e:
            self.test("Settings tests work", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all E11 & E12 backend tests"""
        print("=" * 80)
        print("BACKEND API TESTS - E11 & E12 (Import Session + Bulk Actions + Settings)")
        print("=" * 80)
        
        # Authentication
        if not self.login_admin():
            print("\n❌ Cannot proceed without admin authentication")
            return False
        
        self.login_customer()  # Optional, for 403 tests
        
        # E12 Tests
        print("\n" + "=" * 80)
        print("E12: IMPORT SESSION TESTS")
        print("=" * 80)
        self.test_analyze_with_session()
        self.test_validate_with_session()
        self.test_tiers_with_session()
        self.test_session_rows()
        self.test_session_cells()
        self.test_session_fill()
        self.test_session_close()
        self.test_deviant_cases()
        
        # E11 Tests
        print("\n" + "=" * 80)
        print("E11: BULK ACTIONS + SETTINGS TESTS")
        print("=" * 80)
        self.test_bulk_status()
        self.test_settings_inspired_by()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 80)
        
        if self.tests_passed == self.tests_run:
            print("✓ All E11 & E12 backend tests passed!")
            return True
        else:
            print(f"✗ {self.tests_run - self.tests_passed} test(s) failed")
            return False


def main():
    tester = APITester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
