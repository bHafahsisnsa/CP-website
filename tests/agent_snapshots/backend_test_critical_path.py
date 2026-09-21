"""backend_test_critical_path.py — Comprehensive API testing for Collector Parfum CRITICAL PATH.

Tests all critical endpoints for the customer purchase journey and CMS serving:
1. CMS Content (GET /api/content)
2. Products Catalog (GET /api/products with filters)
3. Product Detail (GET /api/products/:slug)
4. Occasions & Characters (GET /api/occasions, /api/characters)
5. Shipping & Payment Methods (GET /api/shipping-methods, /api/payment-methods)
6. Vouchers (GET /api/vouchers)
7. Order Creation (POST /api/orders)
8. Order History (GET /api/orders)
9. Admin CMS Update (PUT /api/admin/content/:key)
"""
import os
import sys
import httpx
from typing import Dict, Any

BASE_URL = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/") + "/api"  # env-driven (jangan hardcode URL preview)
CUSTOMER_CREDS = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}
ADMIN_CREDS = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}

class CriticalPathTester:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        self.customer_token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_order_code = None
        self.test_voucher_code = None
        
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
    
    def login_customer(self):
        """Login as customer and get token"""
        print("\n=== CUSTOMER AUTHENTICATION ===")
        try:
            r = self.client.post("/auth/login", json=CUSTOMER_CREDS)
            if r.status_code == 200:
                data = r.json()
                self.customer_token = data.get("token")
                return self.test("Customer login successful", bool(self.customer_token))
            else:
                return self.test("Customer login successful", False, f"Status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            return self.test("Customer login successful", False, str(e))
    
    def login_admin(self):
        """Login as admin and get token"""
        print("\n=== ADMIN AUTHENTICATION ===")
        try:
            r = self.client.post("/auth/login", json=ADMIN_CREDS)
            if r.status_code == 200:
                data = r.json()
                self.admin_token = data.get("token")
                return self.test("Admin login successful", bool(self.admin_token))
            else:
                return self.test("Admin login successful", False, f"Status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            return self.test("Admin login successful", False, str(e))
    
    def test_cms_content(self):
        """Test GET /api/content - verify all CMS sections are present"""
        print("\n=== TEST: GET /api/content (CMS SERVING) ===")
        try:
            r = self.client.get("/content")
            if not self.test("GET /content returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            content = r.json()
            
            # Check critical sections exist
            critical_sections = [
                "announcement", "header", "footer", "hero", "marquee_words",
                "category_section", "occasion_section", "character_section",
                "testimonials", "faq"
            ]
            
            for section in critical_sections:
                self.test(f"CMS section '{section}' exists", section in content, 
                         f"Missing section: {section}")
            
            # Check hero section has required fields
            hero = content.get("hero", {})
            self.test("Hero has title", bool(hero.get("title")))
            self.test("Hero has subtitle", bool(hero.get("subtitle")))
            self.test("Hero has primary_label", bool(hero.get("primary_label")))
            
            # Check announcement bar has items
            announcement = content.get("announcement", {})
            items = announcement.get("items", [])
            self.test("Announcement bar has items", len(items) > 0, f"Got {len(items)} items")
            
            return True
        except Exception as e:
            self.test("GET /content works", False, str(e))
            return False
    
    def test_products_list(self):
        """Test GET /api/products - verify product grid loads"""
        print("\n=== TEST: GET /api/products (SHOP PAGE) ===")
        try:
            r = self.client.get("/products")
            if not self.test("GET /products returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            products = r.json()
            self.test("Products list has 12 items", len(products) >= 12, f"Got {len(products)} products")
            
            # Check all products have required fields
            if products:
                p = products[0]
                self.test("Product has id", bool(p.get("id")))
                self.test("Product has name", bool(p.get("name")))
                self.test("Product has slug", bool(p.get("slug")))
                self.test("Product has price", isinstance(p.get("price"), int))
                # images boleh kosong BY DESIGN: FE menurunkan bottle-art SVG generatif
                # (lihat frontend/src/services/catalog.js normalizeProduct → deriveImages).
                self.test("Product has images list", isinstance(p.get("images"), list))
                self.test("Product has options[]", isinstance(p.get("options"), list))
                self.test("Product has variants[]", isinstance(p.get("variants"), list) and len(p.get("variants", [])) > 0)
            
            return True
        except Exception as e:
            self.test("GET /products works", False, str(e))
            return False
    
    def test_products_filters(self):
        """Test GET /api/products with filters"""
        print("\n=== TEST: GET /api/products (WITH FILTERS) ===")
        try:
            # Test category filter
            r = self.client.get("/products?category=woody")
            self.test("Category filter works", r.status_code == 200)
            
            # Test gender filter
            r = self.client.get("/products?gender=pria")
            self.test("Gender filter works", r.status_code == 200)
            
            # Test price range filter
            r = self.client.get("/products?min_price=300000&max_price=800000")
            self.test("Price range filter works", r.status_code == 200)
            
            # Test sorting
            r = self.client.get("/products?sort=low")
            self.test("Sort by price (low) works", r.status_code == 200)
            
            return True
        except Exception as e:
            self.test("Product filters work", False, str(e))
            return False
    
    def test_product_detail(self):
        """Test GET /api/products/:slug - verify PDP loads with variant selector"""
        print("\n=== TEST: GET /api/products/:slug (PDP) ===")
        try:
            # Get first product slug
            r = self.client.get("/products")
            products = r.json()
            if not products:
                self.test("Product detail test", False, "No products found")
                return False
            
            slug = products[0].get("slug")
            r = self.client.get(f"/products/{slug}")
            
            if not self.test(f"GET /products/{slug} returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            product = r.json()
            
            # Check N-dimensional variant system
            options = product.get("options", [])
            variants = product.get("variants", [])
            
            self.test("Product has options[] (N-dimensional)", len(options) > 0, f"Got {len(options)} options")
            self.test("Product has variants[]", len(variants) > 0, f"Got {len(variants)} variants")
            
            # Check all variants have SKU
            if variants:
                all_have_sku = all(v.get("sku") for v in variants)
                self.test("All variants have SKU", all_have_sku)
                
                # Check variant structure
                v = variants[0]
                self.test("Variant has options{}", isinstance(v.get("options"), dict))
                self.test("Variant has price", isinstance(v.get("price"), int) and v.get("price") > 0)
                self.test("Variant has stock", isinstance(v.get("stock"), int) and v.get("stock") >= 0)
            
            # Check price range
            self.test("Product has price_min", isinstance(product.get("price_min"), int))
            self.test("Product has price_max", isinstance(product.get("price_max"), int))
            
            # Check notes pyramid
            notes = product.get("notes", {})
            self.test("Product has notes.top", isinstance(notes.get("top"), list))
            self.test("Product has notes.heart", isinstance(notes.get("heart"), list))
            self.test("Product has notes.base", isinstance(notes.get("base"), list))
            
            return True
        except Exception as e:
            self.test("GET /products/:slug works", False, str(e))
            return False
    
    def test_occasions_characters(self):
        """Test GET /api/occasions and /api/characters"""
        print("\n=== TEST: GET /api/occasions & /api/characters ===")
        try:
            # Test occasions
            r = self.client.get("/occasions")
            if not self.test("GET /occasions returns 200", r.status_code == 200):
                return False
            
            occasions = r.json()
            self.test("Occasions list has 8 items", len(occasions) >= 8, f"Got {len(occasions)} occasions")
            
            if occasions:
                o = occasions[0]
                self.test("Occasion has id", bool(o.get("id")))
                self.test("Occasion has name", bool(o.get("name")))
                self.test("Occasion has slug", bool(o.get("slug")))
            
            # Test characters
            r = self.client.get("/characters")
            if not self.test("GET /characters returns 200", r.status_code == 200):
                return False
            
            characters = r.json()
            self.test("Characters list has 12 items", len(characters) >= 12, f"Got {len(characters)} characters")
            
            if characters:
                c = characters[0]
                self.test("Character has id", bool(c.get("id")))
                self.test("Character has name", bool(c.get("name")))
                self.test("Character has slug", bool(c.get("slug")))
            
            return True
        except Exception as e:
            self.test("Occasions/Characters endpoints work", False, str(e))
            return False
    
    def test_shipping_payment_methods(self):
        """Test GET /api/shipping-methods and /api/payment-methods"""
        print("\n=== TEST: GET /api/shipping-methods & /api/payment-methods ===")
        try:
            # Test shipping methods
            r = self.client.get("/shipping-methods")
            if not self.test("GET /shipping-methods returns 200", r.status_code == 200):
                return False
            
            shipping = r.json()
            self.test("Shipping methods list has 5 items", len(shipping) >= 5, f"Got {len(shipping)} methods")
            
            if shipping:
                s = shipping[0]
                self.test("Shipping method has id", bool(s.get("id")))
                self.test("Shipping method has name", bool(s.get("name")))
                self.test("Shipping method has price", isinstance(s.get("price"), int))
                self.test("Shipping method has eta", bool(s.get("eta")))
            
            # Test payment methods
            r = self.client.get("/payment-methods")
            if not self.test("GET /payment-methods returns 200", r.status_code == 200):
                return False
            
            payment = r.json()
            self.test("Payment methods list has 8 items", len(payment) >= 8, f"Got {len(payment)} methods")
            
            if payment:
                p = payment[0]
                self.test("Payment method has id", bool(p.get("id")))
                self.test("Payment method has name", bool(p.get("name")))
                self.test("Payment method has group", p.get("group") in ["transfer", "ewallet", "cod"])
            
            return True
        except Exception as e:
            self.test("Shipping/Payment methods endpoints work", False, str(e))
            return False
    
    def test_vouchers(self):
        """Test GET /api/vouchers"""
        print("\n=== TEST: GET /api/vouchers ===")
        try:
            r = self.client.get("/vouchers")
            if not self.test("GET /vouchers returns 200", r.status_code == 200):
                return False
            
            vouchers = r.json()
            # Seed = 6 voucher, tapi 1 (EXPIRED2024) sengaja kedaluwarsa sebagai data uji
            # window — API publik BENAR memfilternya. Ekspektasi: >=5 dan EXPIRED2024 absen.
            codes = [v.get("code") for v in vouchers]
            self.test("Vouchers list has >=5 valid items", len(vouchers) >= 5, f"Got {len(vouchers)} vouchers")
            self.test("Expired voucher filtered out", "EXPIRED2024" not in codes, f"codes={codes}")
            
            if vouchers:
                v = vouchers[0]
                self.test("Voucher has code", bool(v.get("code")))
                self.test("Voucher has type", v.get("type") in ["percent", "flat", "free_shipping"])
                self.test("Voucher has label", bool(v.get("label")))
                
                # Store a voucher code for order test
                self.test_voucher_code = v.get("code")
            
            return True
        except Exception as e:
            self.test("GET /vouchers works", False, str(e))
            return False
    
    def test_create_order_guest(self):
        """Test POST /api/orders as guest (no auth)"""
        print("\n=== TEST: POST /api/orders (GUEST CHECKOUT) ===")
        try:
            # Get a product with available stock
            r = self.client.get("/products")
            products = r.json()
            if not products:
                self.test("Order creation test", False, "No products found")
                return False
            
            # Find product with stock
            product = None
            for p in products:
                variants = p.get("variants", [])
                if variants and any(v.get("stock", 0) > 0 for v in variants):
                    product = p
                    break
            
            if not product:
                self.test("Order creation test", False, "No products with stock found")
                return False
            
            # Get first variant with stock
            variant = next((v for v in product.get("variants", []) if v.get("stock", 0) > 0), None)
            if not variant:
                self.test("Order creation test", False, "No variant with stock found")
                return False
            
            # Get shipping and payment methods
            r_ship = self.client.get("/shipping-methods")
            shipping_methods = r_ship.json()
            
            r_pay = self.client.get("/payment-methods")
            payment_methods = r_pay.json()
            
            if not shipping_methods or not payment_methods:
                self.test("Order creation test", False, "No shipping/payment methods found")
                return False
            
            order_payload = {
                "items": [
                    {
                        "product_id": product.get("id"),
                        "sku": variant.get("sku"),
                        "quantity": 1
                    }
                ],
                "address": {
                    "name": "Test Customer",
                    "phone": "081234567890",
                    "street": "Jl. Test No. 123",
                    "city": "Jakarta Pusat",
                    "province": "DKI Jakarta",
                    "postal": "10110"
                },
                "shipping_id": shipping_methods[0].get("id"),
                "payment": {
                    "group": payment_methods[0].get("group"),
                    "method_id": payment_methods[0].get("id")
                }
            }
            
            r = self.client.post("/orders", json=order_payload)
            
            if not self.test("POST /orders returns 200/201", r.status_code in (200, 201),
                            f"Status: {r.status_code}, Response: {r.text[:500]}"):
                return False
            
            order = r.json()
            self.test_order_code = order.get("code")
            
            self.test("Order has code", bool(order.get("code")))
            self.test("Order has status=pending", order.get("status") == "pending")
            self.test("Order has items", len(order.get("items", [])) > 0)
            self.test("Order has subtotal", isinstance(order.get("subtotal"), int) and order.get("subtotal") > 0)
            self.test("Order has total", isinstance(order.get("total"), int) and order.get("total") > 0)
            self.test("Order has address", isinstance(order.get("address"), dict))
            self.test("Order has shipping", isinstance(order.get("shipping"), dict))
            self.test("Order has payment", isinstance(order.get("payment"), dict))
            
            # Verify order item has correct structure
            if order.get("items"):
                item = order["items"][0]
                self.test("Order item has sku", bool(item.get("sku")))
                self.test("Order item has options{}", isinstance(item.get("options"), dict))
                self.test("Order item has unit_price", isinstance(item.get("unit_price"), int))
                self.test("Order item has volume_ml", isinstance(item.get("volume_ml"), int))
            
            return True
        except Exception as e:
            self.test("POST /orders works", False, str(e))
            return False
    
    def test_order_history(self):
        """Test GET /api/orders (requires customer login)"""
        print("\n=== TEST: GET /api/orders (ORDER HISTORY) ===")
        if not self.customer_token:
            print("Skipping order history test - customer not logged in")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.customer_token}"}
            r = self.client.get("/orders", headers=headers)
            
            if not self.test("GET /orders returns 200", r.status_code == 200, f"Status: {r.status_code}"):
                return False
            
            orders = r.json()
            self.test("Orders list is array", isinstance(orders, list))
            
            if orders:
                order = orders[0]
                self.test("Order has code", bool(order.get("code")))
                self.test("Order has status", bool(order.get("status")))
                self.test("Order has created_at", bool(order.get("created_at")))
            
            return True
        except Exception as e:
            self.test("GET /orders works", False, str(e))
            return False
    
    def test_admin_cms_update(self):
        """Test PUT /api/admin/content/:key (CMS SERVING - ADMIN EDIT ROUNDTRIP)"""
        print("\n=== TEST: PUT /api/admin/content/:key (CMS ADMIN EDIT) ===")
        if not self.admin_token:
            print("Skipping CMS update test - admin not logged in")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get current content
            r = self.client.get("/admin/content", headers=headers)
            if not self.test("GET /admin/content returns 200", r.status_code == 200):
                return False
            
            content = r.json()
            
            # Update hero section with distinctive value.
            # KONTRAK API: PUT /admin/content/{key} menerima {"data": {...}} (ContentUpdateIn)
            # dan merespons {"key", "data"} — bukan field top-level.
            test_value = "TEST_HERO_TITLE_E2E_12345"
            hero_update = {"data": {
                "title": test_value,
                "title_accent": "Dari layar ke kulit.",
                "subtitle": "Test subtitle for E2E testing"
            }}
            
            r = self.client.put("/admin/content/hero", json=hero_update, headers=headers)
            
            if not self.test("PUT /admin/content/hero returns 200", r.status_code == 200,
                            f"Status: {r.status_code}, Response: {r.text[:500]}"):
                return False
            
            updated = (r.json() or {}).get("data", {})
            self.test("Updated hero has test title", updated.get("title") == test_value,
                     f"Expected '{test_value}', got '{updated.get('title')}'")
            
            # Verify the change is reflected in public content
            r = self.client.get("/content")
            public_content = r.json()
            public_hero = public_content.get("hero", {})
            
            self.test("Public content reflects admin edit", public_hero.get("title") == test_value,
                     f"Expected '{test_value}', got '{public_hero.get('title')}'")
            
            # Restore original value
            original_hero = content.get("hero", {})
            r = self.client.put("/admin/content/hero", json={"data": original_hero}, headers=headers)
            self.test("Hero content restored", r.status_code == 200)
            
            return True
        except Exception as e:
            self.test("PUT /admin/content/:key works", False, str(e))
            return False
    
    def test_no_5xx_errors(self):
        """Test that critical endpoints don't return 5xx errors"""
        print("\n=== TEST: NO 5xx ERRORS ON CRITICAL ENDPOINTS ===")
        try:
            endpoints = [
                "/content",
                "/products",
                "/occasions",
                "/characters",
                "/shipping-methods",
                "/payment-methods",
                "/vouchers"
            ]
            
            all_ok = True
            for endpoint in endpoints:
                r = self.client.get(endpoint)
                is_ok = r.status_code < 500
                self.test(f"{endpoint} returns < 500", is_ok, f"Status: {r.status_code}")
                all_ok = all_ok and is_ok
            
            return all_ok
        except Exception as e:
            self.test("No 5xx errors test", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all critical path backend tests"""
        print("=" * 80)
        print("BACKEND API TESTS - COLLECTOR PARFUM CRITICAL PATH & CMS SERVING")
        print("=" * 80)
        
        # Authentication
        self.login_customer()
        self.login_admin()
        
        # Run all tests
        self.test_cms_content()
        self.test_products_list()
        self.test_products_filters()
        self.test_product_detail()
        self.test_occasions_characters()
        self.test_shipping_payment_methods()
        self.test_vouchers()
        self.test_create_order_guest()
        self.test_order_history()
        self.test_admin_cms_update()
        self.test_no_5xx_errors()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 80)
        
        if self.tests_passed == self.tests_run:
            print("✓ All backend critical path tests passed!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"✗ {failed} test(s) failed")
            return False

def main():
    tester = CriticalPathTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
