"""test_variant_matrix.py — Test two-dimensional variant matrix (Type x Size) for Collector Parfum.

Tests the variant matrix feature where products can have:
- TYPED variants: type (Standard/Premium) x ml (30/50/100) with per-variant price/stock/SKU
- TYPELESS variants: only ml (backward compatible)
- Auto-generated unique SKUs per variant
- Anti-oversell keyed by (type, ml)
"""
import os

import requests
import sys
from datetime import datetime

# Baca dari env (jangan hardcode URL preview) — fallback ke backend lokal.
BASE_URL = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/") + "/api"

class VariantMatrixTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.admin_token = None

    def log_pass(self, name):
        self.tests_passed += 1
        print(f"✅ PASS: {name}")

    def log_fail(self, name, reason):
        self.tests_failed += 1
        self.failures.append({"test": name, "reason": reason})
        print(f"❌ FAIL: {name}")
        print(f"   Reason: {reason}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{BASE_URL}{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            else:
                self.log_fail(name, f"Unsupported method: {method}")
                return False, None

            print(f"   Status: {response.status_code} (expected: {expected_status})")
            
            if response.status_code != expected_status:
                try:
                    body = response.json()
                    self.log_fail(name, f"Expected {expected_status}, got {response.status_code}. Response: {body}")
                except Exception:
                    self.log_fail(name, f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:300]}")
                return False, None

            try:
                json_response = response.json()
                self.log_pass(name)
                return True, json_response
            except Exception:
                if expected_status == 204:
                    self.log_pass(name)
                    return True, None
                self.log_fail(name, "Response is not valid JSON")
                return False, None

        except requests.exceptions.Timeout:
            self.log_fail(name, "Request timeout")
            return False, None
        except requests.exceptions.ConnectionError:
            self.log_fail(name, "Connection error")
            return False, None
        except Exception as e:
            self.log_fail(name, f"Exception: {str(e)}")
            return False, None

    def setup_admin_auth(self):
        """Login as admin to get token"""
        print("\n" + "="*60)
        print("SETUP: Admin Authentication")
        print("="*60)
        
        success, response = self.run_test(
            "Login as admin@collectorparfum.id",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )
        
        if success and response and "token" in response:
            self.admin_token = response["token"]
            print(f"   ✓ Admin token obtained: {self.admin_token[:20]}...")
            return True
        else:
            print("   ❌ Failed to obtain admin token")
            return False

    def test_noir_oud_intense_typed_variants(self):
        """Test GET /api/products/noir-oud-intense returns 6 typed variants"""
        print("\n" + "="*60)
        print("TEST 1: Noir Oud Intense - Typed Variants (Standard/Premium x 30/50/100)")
        print("="*60)
        
        success, response = self.run_test(
            "GET /api/products/noir-oud-intense",
            "GET",
            "/products/noir-oud-intense",
            200
        )
        
        if not success or not response:
            return
        
        # Check volumes array
        volumes = response.get("volumes", [])
        print(f"   Found {len(volumes)} volumes")
        
        if len(volumes) != 6:
            self.log_fail("Noir Oud Intense volume count", f"Expected 6 volumes, got {len(volumes)}")
            return
        
        # Check each volume has required fields
        required_fields = ["type", "ml", "price", "stock", "compare_at_price", "sku"]
        for i, vol in enumerate(volumes):
            missing = [f for f in required_fields if f not in vol]
            if missing:
                self.log_fail(f"Volume {i+1} structure", f"Missing fields: {missing}")
            else:
                print(f"   ✓ Volume {i+1}: type='{vol['type']}', ml={vol['ml']}, price={vol['price']}, stock={vol['stock']}, sku={vol['sku']}")
        
        # Check for Standard and Premium types
        types = set(v.get("type", "") for v in volumes)
        # Model N-dimensi: label komposit (mis. 'EDP / Standard') → cek substring.
        if not any("Standard" in t for t in types) or not any("Premium" in t for t in types):
            self.log_fail("Noir Oud Intense types", f"Expected 'Standard' and 'Premium' present, got {types}")
        else:
            print(f"   ✓ Found types: {types}")
        
        # Check product-level price is cheapest variant
        product_price = response.get("price")
        min_variant_price = min(v["price"] for v in volumes)
        if product_price != min_variant_price:
            self.log_fail("Product price", f"Expected product price={min_variant_price} (cheapest variant), got {product_price}")
        else:
            print(f"   ✓ Product price={product_price} matches cheapest variant")
        
        # Check SKUs are unique
        skus = [v.get("sku") for v in volumes if v.get("sku")]
        if len(skus) != len(set(skus)):
            self.log_fail("SKU uniqueness", f"Duplicate SKUs found: {skus}")
        else:
            print(f"   ✓ All SKUs are unique: {skus}")

    def test_create_typed_product(self):
        """Test POST /api/admin/products - create typed product with auto-generated SKUs"""
        print("\n" + "="*60)
        print("TEST 2: Create Typed Product (Standard/Premium x 30/50)")
        print("="*60)
        
        if not self.admin_token:
            self.log_fail("Create typed product", "No admin token available")
            return
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        product_data = {
            "name": f"Test Typed Product {timestamp}",
            "slug": f"test-typed-{timestamp}",
            "category": "woody",
            "concentration": "EDP",
            "gender": "Unisex",
            "description": "Test product with typed variants",
            "volumes": [
                {"type": "Standard", "ml": 30, "price": 300000, "stock": 10},
                {"type": "Standard", "ml": 50, "price": 450000, "stock": 15},
                {"type": "Premium", "ml": 30, "price": 500000, "stock": 8},
                {"type": "Premium", "ml": 50, "price": 750000, "stock": 12}
            ]
        }
        
        success, response = self.run_test(
            "POST /api/admin/products with typed variants",
            "POST",
            "/admin/products",
            200,
            data=product_data,
            headers=headers
        )
        
        if not success or not response:
            return
        
        # Check response volumes have auto-generated SKUs
        volumes = response.get("volumes", [])
        print(f"   Created product with {len(volumes)} volumes")
        
        for vol in volumes:
            if not vol.get("sku"):
                self.log_fail("Auto-generated SKU", f"Volume {vol} missing SKU")
            else:
                print(f"   ✓ Volume: type='{vol['type']}', ml={vol['ml']}, sku={vol['sku']}")
        
        # Check product price is min variant price
        product_price = response.get("price")
        if product_price != 300000:
            self.log_fail("Typed product price", f"Expected 300000 (min variant), got {product_price}")
        else:
            print(f"   ✓ Product price={product_price} (min variant)")
        
        # Store product ID for cleanup
        self.typed_product_id = response.get("id")

    def test_create_typeless_product(self):
        """Test POST /api/admin/products - create typeless product (backward compatible)"""
        print("\n" + "="*60)
        print("TEST 3: Create Typeless Product (only sizes, no types)")
        print("="*60)
        
        if not self.admin_token:
            self.log_fail("Create typeless product", "No admin token available")
            return
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        product_data = {
            "name": f"Test Typeless Product {timestamp}",
            "slug": f"test-typeless-{timestamp}",
            "category": "floral",
            "concentration": "EDT",
            "gender": "Wanita",
            "description": "Test product without types (backward compatible)",
            "volumes": [
                {"ml": 30, "price": 250000, "stock": 20},
                {"ml": 50, "price": 400000, "stock": 25},
                {"ml": 100, "price": 700000, "stock": 15}
            ]
        }
        
        success, response = self.run_test(
            "POST /api/admin/products with typeless variants",
            "POST",
            "/admin/products",
            200,
            data=product_data,
            headers=headers
        )
        
        if not success or not response:
            return
        
        # Check response volumes have type='' (empty string)
        volumes = response.get("volumes", [])
        print(f"   Created product with {len(volumes)} volumes")
        
        # Model N-dimensi: concentration menjadi dimensi → label type komposit = 'EDT'.
        # Produk tanpa dimensi non-ukuran lain dianggap "typeless" bila type '' ATAU
        # hanya berisi concentration.
        for vol in volumes:
            vol_type = vol.get("type", "")
            if vol_type not in ("", "EDT"):
                self.log_fail("Typeless variant", f"Expected type ''/'EDT' (concentration-only), got type='{vol_type}'")
            else:
                print(f"   ✓ Volume: type='{vol_type}', ml={vol['ml']}, sku={vol['sku']}")
        
        # Store product ID
        self.typeless_product_id = response.get("id")

    def test_duplicate_variant_rejection(self):
        """Test POST /api/admin/products - reject duplicate (type,ml) combo"""
        print("\n" + "="*60)
        print("TEST 4: Reject Duplicate (type, ml) Combination")
        print("="*60)
        
        if not self.admin_token:
            self.log_fail("Duplicate variant test", "No admin token available")
            return
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        product_data = {
            "name": f"Test Duplicate {timestamp}",
            "slug": f"test-dup-{timestamp}",
            "category": "woody",
            "volumes": [
                {"type": "Standard", "ml": 50, "price": 300000, "stock": 10},
                {"type": "Standard", "ml": 50, "price": 350000, "stock": 5}  # Duplicate!
            ]
        }
        
        success, response = self.run_test(
            "POST /api/admin/products with duplicate (type,ml)",
            "POST",
            "/admin/products",
            400,
            data=product_data,
            headers=headers
        )
        
        if success and response:
            print(f"   ✓ Correctly rejected: {response}")

    def test_order_typed_variant(self):
        """Test POST /api/orders - order specific typed variant (Premium, 50ml)"""
        print("\n" + "="*60)
        print("TEST 5: Order Specific Typed Variant (Premium, 50ml)")
        print("="*60)
        
        # Order noir-oud-intense Premium 50ml
        order_data = {
            "items": [
                {
                    "product_id": "prd_noiroudintense",
                    "variant_type": "Premium",
                    "volume_ml": 50,
                    "quantity": 1
                }
            ],
            "address": {
                "name": "Test User",
                "phone": "081234567890",
                "street": "Jl. Test No. 123",
                "city": "Jakarta",
                "province": "DKI Jakarta",
                "postal": "12345"
            },
            "shipping_id": "jne-reg",
            "payment": {"group": "transfer", "method_id": "bca"}
        }
        
        success, response = self.run_test(
            "POST /api/orders with typed variant (Premium, 50ml)",
            "POST",
            "/orders",
            200,
            data=order_data
        )
        
        if not success or not response:
            return
        
        # Check order items contain variant_type and sku
        items = response.get("items", [])
        if len(items) == 0:
            self.log_fail("Order items", "No items in order")
            return
        
        item = items[0]
        variant_type = item.get("variant_type")
        sku = item.get("sku")
        unit_price = item.get("unit_price")
        volume_ml = item.get("volume_ml")
        
        print(f"   Order item: variant_type='{variant_type}', volume_ml={volume_ml}, unit_price={unit_price}, sku={sku}")
        
        if "Premium" not in str(variant_type or ""):
            self.log_fail("Order variant_type", f"Expected komposit mengandung 'Premium', got '{variant_type}'")
        
        if volume_ml != 50:
            self.log_fail("Order volume_ml", f"Expected 50, got {volume_ml}")
        
        if unit_price != 785000:
            self.log_fail("Order unit_price", f"Expected 785000 (Premium 50ml price), got {unit_price}")
        
        if not sku:
            self.log_fail("Order SKU", "SKU not set in order item")
        else:
            print(f"   ✓ Order created with correct variant: {response.get('code')}")
        
        # Store order code
        self.typed_order_code = response.get("code")

    def test_order_unknown_variant_type(self):
        """Test POST /api/orders - reject unknown variant_type"""
        print("\n" + "="*60)
        print("TEST 6: Reject Unknown Variant Type (Deluxe)")
        print("="*60)
        
        order_data = {
            "items": [
                {
                    "product_id": "prd_noiroudintense",
                    "variant_type": "Deluxe",  # Unknown type!
                    "volume_ml": 50,
                    "quantity": 1
                }
            ],
            "address": {
                "name": "Test User",
                "phone": "081234567890",
                "street": "Jl. Test No. 123",
                "city": "Jakarta",
                "province": "DKI Jakarta"
            },
            "shipping_id": "jne-reg",
            "payment": {"group": "transfer", "method_id": "bca"}
        }
        
        success, response = self.run_test(
            "POST /api/orders with unknown variant_type",
            "POST",
            "/orders",
            400,
            data=order_data
        )
        
        if success and response:
            print(f"   ✓ Correctly rejected: {response}")

    def test_anti_oversell_by_type_ml(self):
        """Test anti-oversell keyed by (type, ml)"""
        print("\n" + "="*60)
        print("TEST 7: Anti-Oversell by (type, ml)")
        print("="*60)
        
        # First, get current stock of noir-oud-intense Standard 30ml
        success, product = self.run_test(
            "GET noir-oud-intense for stock check",
            "GET",
            "/products/noir-oud-intense",
            200
        )
        
        if not success or not product:
            return
        
        volumes = product.get("volumes", [])
        standard_30 = next((v for v in volumes
                            if "Standard" in str(v.get("type") or "") and v.get("ml") == 30), None)
        
        if not standard_30:
            self.log_fail("Anti-oversell setup", "Standard 30ml variant not found")
            return
        
        stock = standard_30.get("stock", 0)
        print(f"   Current stock of Standard 30ml: {stock}")
        
        # Try to order more than stock
        order_data = {
            "items": [
                {
                    "product_id": "prd_noiroudintense",
                    "variant_type": "Standard",
                    "volume_ml": 30,
                    "quantity": stock + 10  # Exceed stock
                }
            ],
            "address": {
                "name": "Test User",
                "phone": "081234567890",
                "street": "Jl. Test No. 123",
                "city": "Jakarta",
                "province": "DKI Jakarta"
            },
            "shipping_id": "jne-reg",
            "payment": {"group": "transfer", "method_id": "bca"}
        }
        
        success, response = self.run_test(
            "POST /api/orders with quantity > stock",
            "POST",
            "/orders",
            409,
            data=order_data
        )
        
        if success and response:
            # Check response contains variant_type, volume_ml, available (nested in 'detail')
            detail = response.get("detail", {})
            if isinstance(detail, dict):
                if "variant_type" not in detail or "volume_ml" not in detail or "available" not in detail:
                    self.log_fail("Anti-oversell response", f"Missing fields in 409 response detail: {detail}")
                else:
                    print(f"   ✓ Stock conflict: variant_type={detail.get('variant_type')}, volume_ml={detail.get('volume_ml')}, available={detail.get('available')}")
            else:
                self.log_fail("Anti-oversell response", f"Expected detail to be dict, got: {response}")

    def cleanup(self):
        """Bersihkan data sintetis (produk test + order test) agar DB tetap pristine."""
        print("\n" + "="*60)
        print("CLEANUP: menghapus data sintetis test")
        print("="*60)
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        for pid in [getattr(self, "typed_product_id", None), getattr(self, "typeless_product_id", None)]:
            if pid:
                try:
                    r = requests.delete(f"{BASE_URL}/admin/products/{pid}", headers=headers, timeout=15)
                    print(f"   delete product {pid}: HTTP {r.status_code}")
                except Exception as e:
                    print(f"   delete product {pid} gagal: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("VARIANT MATRIX TEST SUMMARY")
        print("="*60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        
        if self.tests_run > 0:
            print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print("\n" + "="*60)
            print("FAILED TESTS DETAILS")
            print("="*60)
            for failure in self.failures:
                print(f"\n❌ {failure['test']}")
                print(f"   {failure['reason']}")
        
        return 0 if self.tests_failed == 0 else 1


def main():
    tester = VariantMatrixTester()
    
    # Setup admin authentication
    if not tester.setup_admin_auth():
        print("\n❌ Cannot proceed without admin authentication")
        return 1
    
    # Run tests
    try:
        tester.test_noir_oud_intense_typed_variants()
        tester.test_create_typed_product()
        tester.test_create_typeless_product()
        tester.test_duplicate_variant_rejection()
        tester.test_order_typed_variant()
        tester.test_order_unknown_variant_type()
        tester.test_anti_oversell_by_type_ml()
    finally:
        tester.cleanup()
    
    # Print summary
    return tester.print_summary()


if __name__ == "__main__":
    sys.exit(main())
