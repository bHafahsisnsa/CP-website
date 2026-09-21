"""backend_test.py — Epic E1/E2/E3/E4/E7 backend testing for Collector Parfum.

Tests catalog endpoints (products, categories, reviews), vouchers, orders/cart/checkout, account (profile, addresses, wishlist), and E7 (analytics, sitemap, CRM).
"""
import os
import requests
import sys
from datetime import datetime

BASE_URL = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/") + "/api"  # env-driven (jangan hardcode URL preview)

class FoundationTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.token = None

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
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                self.log_fail(name, f"Unsupported method: {method}")
                return False, None

            print(f"   Status: {response.status_code} (expected: {expected_status})")
            
            if response.status_code != expected_status:
                try:
                    body = response.json()
                    self.log_fail(name, f"Expected {expected_status}, got {response.status_code}. Response: {body}")
                except Exception:
                    self.log_fail(name, f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}")
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

    def test_health_endpoints(self):
        """Test health endpoints"""
        print("\n" + "="*60)
        print("TESTING HEALTH ENDPOINTS")
        print("="*60)

        # Test GET /api/
        success, response = self.run_test(
            "GET /api/ returns 200 with service info",
            "GET",
            "/",
            200
        )
        if success and response:
            if not all(k in response for k in ["service", "status", "message"]):
                self.log_fail("GET /api/ response structure", f"Missing required fields. Got: {response}")
            else:
                print(f"   Response: {response}")

        # Test GET /api/health
        success, response = self.run_test(
            "GET /api/health returns 200 with health info",
            "GET",
            "/health",
            200
        )
        if success and response:
            if not all(k in response for k in ["status", "db", "time"]):
                self.log_fail("GET /api/health response structure", f"Missing required fields. Got: {response}")
            else:
                print(f"   Response: {response}")
                if not response.get("db"):
                    print("   ⚠️  WARNING: Database connection is not healthy")

    def test_register_success(self):
        """Test successful registration"""
        print("\n" + "="*60)
        print("TESTING REGISTRATION - SUCCESS CASES")
        print("="*60)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_email = f"test{timestamp}@example.com"
        
        success, response = self.run_test(
            "POST /api/auth/register with valid data returns 200",
            "POST",
            "/auth/register",
            200,
            data={
                "name": "Test User",
                "email": test_email,
                "password": "Test123!",
                "phone": "081234567890"
            }
        )
        
        if success and response:
            # Check response structure
            if "token" not in response or "user" not in response:
                self.log_fail("Register response structure", f"Missing token or user. Got: {response}")
            else:
                print(f"   Token: {response['token'][:20]}...")
                
                # Check token format
                if not response["token"].startswith("sess_"):
                    self.log_fail("Register token format", f"Token should start with 'sess_', got: {response['token'][:10]}")
                
                # Check user object
                user = response["user"]
                print(f"   User: {user}")
                
                if user.get("role") != "customer":
                    self.log_fail("Register user role", f"Expected role='customer', got: {user.get('role')}")
                
                if "password_hash" in user:
                    self.log_fail("Register security", "Response contains password_hash (security leak!)")
                
                if user.get("email") != test_email:
                    self.log_fail("Register user email", f"Expected email={test_email}, got: {user.get('email')}")
                
                # Store token for later tests
                self.token = response["token"]

    def test_register_duplicate(self):
        """Test registration with duplicate email"""
        print("\n" + "="*60)
        print("TESTING REGISTRATION - DUPLICATE EMAIL")
        print("="*60)

        # Try to register with admin email (already seeded)
        success, response = self.run_test(
            "POST /api/auth/register with duplicate email returns 409",
            "POST",
            "/auth/register",
            409,
            data={
                "name": "Duplicate User",
                "email": "admin@collectorparfum.id",
                "password": "Test123!"
            }
        )

    def test_register_validation(self):
        """Test registration validation"""
        print("\n" + "="*60)
        print("TESTING REGISTRATION - VALIDATION")
        print("="*60)

        # Test missing password
        success, response = self.run_test(
            "POST /api/auth/register without password returns 422",
            "POST",
            "/auth/register",
            422,
            data={
                "name": "Test User",
                "email": "test@example.com"
            }
        )

        # Test short password
        success, response = self.run_test(
            "POST /api/auth/register with password < 6 chars returns 422",
            "POST",
            "/auth/register",
            422,
            data={
                "name": "Test User",
                "email": "test2@example.com",
                "password": "12345"
            }
        )

        # Test invalid email
        success, response = self.run_test(
            "POST /api/auth/register with invalid email returns 422",
            "POST",
            "/auth/register",
            422,
            data={
                "name": "Test User",
                "email": "not-an-email",
                "password": "Test123!"
            }
        )

    def test_login_success(self):
        """Test successful login"""
        print("\n" + "="*60)
        print("TESTING LOGIN - SUCCESS CASES")
        print("="*60)

        # Test admin login
        success, response = self.run_test(
            "POST /api/auth/login with admin credentials returns 200",
            "POST",
            "/auth/login",
            200,
            data={
                "email": "admin@collectorparfum.id",
                "password": "Admin#2026"
            }
        )
        
        if success and response:
            if "token" not in response or "user" not in response:
                self.log_fail("Login response structure", f"Missing token or user. Got: {response}")
            else:
                print(f"   Token: {response['token'][:20]}...")
                
                user = response["user"]
                print(f"   User: {user}")
                
                if user.get("role") != "admin":
                    self.log_fail("Login admin role", f"Expected role='admin', got: {user.get('role')}")
                
                if "password_hash" in user:
                    self.log_fail("Login security", "Response contains password_hash (security leak!)")
                
                # Store admin token for /me test
                self.admin_token = response["token"]

        # Test customer login
        success, response = self.run_test(
            "POST /api/auth/login with customer credentials returns 200",
            "POST",
            "/auth/login",
            200,
            data={
                "email": "customer@collectorparfum.id",
                "password": "Customer#2026"
            }
        )

    def test_login_failures(self):
        """Test login failure cases"""
        print("\n" + "="*60)
        print("TESTING LOGIN - FAILURE CASES")
        print("="*60)

        # Test wrong password
        success, response = self.run_test(
            "POST /api/auth/login with wrong password returns 401",
            "POST",
            "/auth/login",
            401,
            data={
                "email": "admin@collectorparfum.id",
                "password": "WrongPassword123"
            }
        )

        # Test non-existent email
        success, response = self.run_test(
            "POST /api/auth/login with non-existent email returns 401",
            "POST",
            "/auth/login",
            401,
            data={
                "email": "nonexistent@example.com",
                "password": "SomePassword123"
            }
        )

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        print("\n" + "="*60)
        print("TESTING /auth/me ENDPOINT")
        print("="*60)

        # Test with valid token
        if hasattr(self, 'admin_token'):
            success, response = self.run_test(
                "GET /api/auth/me with valid token returns 200",
                "GET",
                "/auth/me",
                200,
                headers={
                    "Authorization": f"Bearer {self.admin_token}"
                }
            )
            
            if success and response:
                print(f"   User: {response}")
                if "password_hash" in response:
                    self.log_fail("/auth/me security", "Response contains password_hash (security leak!)")
        else:
            self.log_fail("GET /api/auth/me with valid token", "No admin token available from previous tests")

        # Test without Authorization header
        success, response = self.run_test(
            "GET /api/auth/me without Authorization returns 401",
            "GET",
            "/auth/me",
            401
        )

        # Test with invalid token
        success, response = self.run_test(
            "GET /api/auth/me with invalid token returns 401",
            "GET",
            "/auth/me",
            401,
            headers={
                "Authorization": "Bearer sess_invalid_garbage_token_12345"
            }
        )

    def test_products_list(self):
        """Test GET /api/products basic functionality"""
        print("\n" + "="*60)
        print("TESTING PRODUCTS LIST - BASIC")
        print("="*60)

        success, response = self.run_test(
            "GET /api/products returns 200 with array",
            "GET",
            "/products",
            200
        )
        
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Products list type", f"Expected array, got: {type(response)}")
            else:
                print(f"   Returned {len(response)} products")
                
                # Check for 12 active products
                if len(response) < 12:
                    self.log_fail("Products count", f"Expected at least 12 products, got {len(response)}")
                
                # Check first product structure
                if len(response) > 0:
                    p = response[0]
                    required_fields = ['id', 'slug', 'name', 'category', 'price', 'volumes', 
                                     'notes', 'rating_avg', 'rating_count', 'images', 'status']
                    missing = [f for f in required_fields if f not in p]
                    if missing:
                        self.log_fail("Product structure", f"Missing fields: {missing}")
                    else:
                        print(f"   Sample product: {p.get('name')} (id: {p.get('id')})")
                        
                        # Check id prefix
                        if not p.get('id', '').startswith('prd_'):
                            self.log_fail("Product ID prefix", f"Expected 'prd_' prefix, got: {p.get('id')}")
                        
                        # Check status is active
                        if p.get('status') != 'active':
                            self.log_fail("Product status", f"Expected 'active', got: {p.get('status')}")
                        
                        # Check volumes array
                        if not isinstance(p.get('volumes'), list) or len(p.get('volumes', [])) == 0:
                            self.log_fail("Product volumes", f"Expected non-empty array, got: {p.get('volumes')}")

    def test_products_header(self):
        """Test X-Total-Count header"""
        print("\n" + "="*60)
        print("TESTING PRODUCTS - X-TOTAL-COUNT HEADER")
        print("="*60)

        try:
            url = f"{BASE_URL}/products"
            response = requests.get(url, timeout=10)
            
            self.tests_run += 1
            print("\n🔍 Testing: X-Total-Count header presence")
            
            if response.status_code == 200:
                header = response.headers.get('X-Total-Count') or response.headers.get('x-total-count')
                if header:
                    print(f"   X-Total-Count: {header}")
                    self.log_pass("X-Total-Count header present")
                else:
                    self.log_fail("X-Total-Count header", "Header not found in response")
            else:
                self.log_fail("X-Total-Count header test", f"Got status {response.status_code}")
        except Exception as e:
            self.log_fail("X-Total-Count header test", str(e))

    def test_products_filtering(self):
        """Test product filtering"""
        print("\n" + "="*60)
        print("TESTING PRODUCTS - FILTERING")
        print("="*60)

        # Test category filter
        success, response = self.run_test(
            "GET /api/products?category=woody returns filtered results",
            "GET",
            "/products?category=woody",
            200
        )
        if success and response and isinstance(response, list):
            print(f"   Filtered by category=woody: {len(response)} products")

        # Test gender filter
        success, response = self.run_test(
            "GET /api/products?gender=Pria returns filtered results",
            "GET",
            "/products?gender=Pria",
            200
        )
        if success and response and isinstance(response, list):
            print(f"   Filtered by gender=Pria: {len(response)} products")

        # Test CSV multi-value filter
        success, response = self.run_test(
            "GET /api/products?gender=Pria,Wanita returns filtered results",
            "GET",
            "/products?gender=Pria,Wanita",
            200
        )
        if success and response and isinstance(response, list):
            print(f"   Filtered by gender=Pria,Wanita: {len(response)} products")

        # Test concentration filter
        success, response = self.run_test(
            "GET /api/products?concentration=EDP returns filtered results",
            "GET",
            "/products?concentration=EDP",
            200
        )

        # Test price range
        success, response = self.run_test(
            "GET /api/products?min_price=500000&max_price=1000000 returns filtered results",
            "GET",
            "/products?min_price=500000&max_price=1000000",
            200
        )
        if success and response and isinstance(response, list):
            print(f"   Filtered by price range: {len(response)} products")

        # Test best_seller filter
        success, response = self.run_test(
            "GET /api/products?best_seller=1 returns best sellers",
            "GET",
            "/products?best_seller=1",
            200
        )
        if success and response and isinstance(response, list):
            print(f"   Best sellers: {len(response)} products")

        # Test is_new filter
        success, response = self.run_test(
            "GET /api/products?is_new=1 returns new products",
            "GET",
            "/products?is_new=1",
            200
        )

        # Test search query
        success, response = self.run_test(
            "GET /api/products?q=noir returns search results",
            "GET",
            "/products?q=noir",
            200
        )
        if success and response and isinstance(response, list):
            print(f"   Search q=noir: {len(response)} products")

    def test_products_sorting(self):
        """Test product sorting"""
        print("\n" + "="*60)
        print("TESTING PRODUCTS - SORTING")
        print("="*60)

        sorts = ['featured', 'newest', 'best', 'low', 'high']
        for sort_val in sorts:
            success, response = self.run_test(
                f"GET /api/products?sort={sort_val} returns sorted results",
                "GET",
                f"/products?sort={sort_val}",
                200
            )
            if success and response and isinstance(response, list) and len(response) >= 2:
                if sort_val == 'low':
                    # Check ascending price
                    if response[0].get('price', 0) > response[1].get('price', 0):
                        self.log_fail(f"Sort {sort_val}", "Prices not in ascending order")
                elif sort_val == 'high':
                    # Check descending price
                    if response[0].get('price', 0) < response[1].get('price', 0):
                        self.log_fail(f"Sort {sort_val}", "Prices not in descending order")

    def test_products_pagination(self):
        """Test product pagination"""
        print("\n" + "="*60)
        print("TESTING PRODUCTS - PAGINATION")
        print("="*60)

        # Test limit
        success, response = self.run_test(
            "GET /api/products?limit=5 returns 5 products",
            "GET",
            "/products?limit=5",
            200
        )
        if success and response and isinstance(response, list):
            if len(response) != 5:
                self.log_fail("Limit=5", f"Expected 5 products, got {len(response)}")
            else:
                print(f"   Limit=5 returned {len(response)} products")

        # Test skip
        success, response = self.run_test(
            "GET /api/products?skip=5&limit=5 returns next 5 products",
            "GET",
            "/products?skip=5&limit=5",
            200
        )

        # Test limit clamp to 100
        success, response = self.run_test(
            "GET /api/products?limit=999999 clamps to max",
            "GET",
            "/products?limit=999999",
            200
        )
        if success and response and isinstance(response, list):
            if len(response) > 100:
                self.log_fail("Limit clamp", f"Expected max 100, got {len(response)}")

    def test_product_detail(self):
        """Test GET /api/products/{slug}"""
        print("\n" + "="*60)
        print("TESTING PRODUCT DETAIL")
        print("="*60)

        # Test valid slug
        success, response = self.run_test(
            "GET /api/products/noir-oud-intense returns 200",
            "GET",
            "/products/noir-oud-intense",
            200
        )
        if success and response:
            if not isinstance(response, dict):
                self.log_fail("Product detail type", f"Expected object, got: {type(response)}")
            else:
                print(f"   Product: {response.get('name')}")
                if response.get('slug') != 'noir-oud-intense':
                    self.log_fail("Product slug", f"Expected 'noir-oud-intense', got: {response.get('slug')}")

        # Test invalid slug (404)
        success, response = self.run_test(
            "GET /api/products/does-not-exist returns 404",
            "GET",
            "/products/does-not-exist",
            404
        )

    def test_categories(self):
        """Test GET /api/categories"""
        print("\n" + "="*60)
        print("TESTING CATEGORIES")
        print("="*60)

        success, response = self.run_test(
            "GET /api/categories returns 200 with array",
            "GET",
            "/categories",
            200
        )
        
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Categories type", f"Expected array, got: {type(response)}")
            else:
                print(f"   Returned {len(response)} categories")
                
                # Check for 6 active categories
                if len(response) < 6:
                    self.log_fail("Categories count", f"Expected at least 6 categories, got {len(response)}")
                
                # Check first category structure
                if len(response) > 0:
                    c = response[0]
                    required_fields = ['id', 'slug', 'name', 'active']
                    missing = [f for f in required_fields if f not in c]
                    if missing:
                        self.log_fail("Category structure", f"Missing fields: {missing}")
                    else:
                        print(f"   Sample category: {c.get('name')} (id: {c.get('id')})")
                        
                        # Check id prefix
                        if not c.get('id', '').startswith('cat_'):
                            self.log_fail("Category ID prefix", f"Expected 'cat_' prefix, got: {c.get('id')}")

    def test_reviews(self):
        """Test GET /api/reviews"""
        print("\n" + "="*60)
        print("TESTING REVIEWS")
        print("="*60)

        # Test all reviews
        success, response = self.run_test(
            "GET /api/reviews returns 200 with array",
            "GET",
            "/reviews",
            200
        )
        
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Reviews type", f"Expected array, got: {type(response)}")
            else:
                print(f"   Returned {len(response)} reviews")
                
                # Check first review structure
                if len(response) > 0:
                    r = response[0]
                    required_fields = ['id', 'name', 'rating', 'quote', 'status']
                    missing = [f for f in required_fields if f not in r]
                    if missing:
                        self.log_fail("Review structure", f"Missing fields: {missing}")
                    else:
                        print(f"   Sample review: {r.get('name')} - {r.get('rating')} stars")
                        
                        # Check id prefix
                        if not r.get('id', '').startswith('rev_'):
                            self.log_fail("Review ID prefix", f"Expected 'rev_' prefix, got: {r.get('id')}")
                        
                        # Check status is published
                        if r.get('status') != 'published':
                            self.log_fail("Review status", f"Expected 'published', got: {r.get('status')}")

        # Test product-specific reviews
        success, response = self.run_test(
            "GET /api/reviews?product_id=prd_noiroudintense returns filtered reviews",
            "GET",
            "/reviews?product_id=prd_noiroudintense",
            200
        )
        if success and response and isinstance(response, list):
            print(f"   Product-specific reviews: {len(response)}")
            if len(response) != 3:
                print(f"   ⚠️  WARNING: Expected 3 reviews for noir-oud-intense, got {len(response)}")

    def test_adversarial(self):
        """Test adversarial inputs (must never return 5xx)"""
        print("\n" + "="*60)
        print("TESTING ADVERSARIAL INPUTS (MUST NOT 5xx)")
        print("="*60)

        adversarial_tests = [
            ("/products?limit=999999&skip=abc", "huge limit + invalid skip"),
            ("/products?limit=-999", "negative limit"),
            ("/products?sort=DROP%20TABLE", "SQL injection attempt in sort"),
            ("/products?q=🔥💯✨", "emoji in search"),
            ("/products?q=1%20OR%201%3D1", "SQL injection in search"),
            ("/products?min_price=abc&max_price=-1", "invalid price values"),
            ("/products/%00", "null byte in slug"),
            ("/products/../../etc/passwd", "path traversal attempt"),
            ("/reviews?product_id=<script>alert('xss')</script>", "XSS attempt"),
        ]

        for endpoint, description in adversarial_tests:
            try:
                url = f"{BASE_URL}{endpoint}"
                response = requests.get(url, timeout=10)
                
                self.tests_run += 1
                print(f"\n🔍 Testing: {description}")
                print(f"   Endpoint: {endpoint}")
                print(f"   Status: {response.status_code}")
                
                if 500 <= response.status_code < 600:
                    self.log_fail(f"Adversarial: {description}", f"Returned 5xx status: {response.status_code}")
                else:
                    self.log_pass(f"Adversarial: {description} (no 5xx)")
            except Exception as e:
                self.log_fail(f"Adversarial: {description}", f"Exception: {str(e)}")

    def test_vouchers_validate(self):
        """Test POST /api/vouchers/validate with various scenarios"""
        print("\n" + "="*60)
        print("TESTING VOUCHER VALIDATION (Epic E2)")
        print("="*60)

        # Test 1: Valid percent voucher WELCOME10 (10%, no min_spend)
        success, response = self.run_test(
            "POST /api/vouchers/validate - valid percent voucher WELCOME10",
            "POST",
            "/vouchers/validate",
            200,
            data={"code": "WELCOME10", "subtotal": 250000}
        )
        if success and response:
            if not response.get("valid"):
                self.log_fail("WELCOME10 validation", f"Expected valid=true, got {response}")
            elif response.get("type") != "percent":
                self.log_fail("WELCOME10 type", f"Expected type='percent', got {response.get('type')}")
            elif response.get("discount") != 25000:
                self.log_fail("WELCOME10 discount", f"Expected discount=25000, got {response.get('discount')}")
            else:
                print(f"   ✓ Valid percent voucher: discount={response.get('discount')}, code={response.get('code')}")

        # Test 2: Flat voucher COLLECTOR50 below min_spend (min_spend=300000)
        success, response = self.run_test(
            "POST /api/vouchers/validate - COLLECTOR50 below min_spend",
            "POST",
            "/vouchers/validate",
            200,
            data={"code": "COLLECTOR50", "subtotal": 250000}
        )
        if success and response:
            if response.get("valid"):
                self.log_fail("COLLECTOR50 below min_spend", f"Expected valid=false, got {response}")
            elif not response.get("reason"):
                self.log_fail("COLLECTOR50 reason", f"Expected reason for invalid voucher, got {response}")
            else:
                print(f"   ✓ Below min_spend: valid=false, reason={response.get('reason')}")

        # Test 3: Flat voucher COLLECTOR50 at min_spend (should be valid)
        success, response = self.run_test(
            "POST /api/vouchers/validate - COLLECTOR50 at min_spend",
            "POST",
            "/vouchers/validate",
            200,
            data={"code": "COLLECTOR50", "subtotal": 300000}
        )
        if success and response:
            if not response.get("valid"):
                self.log_fail("COLLECTOR50 at min_spend", f"Expected valid=true, got {response}")
            elif response.get("discount") != 50000:
                self.log_fail("COLLECTOR50 discount", f"Expected discount=50000, got {response.get('discount')}")
            else:
                print(f"   ✓ At min_spend: valid=true, discount={response.get('discount')}")

        # Test 4: Free shipping voucher ONGKIRGRATIS (min_spend=150000)
        success, response = self.run_test(
            "POST /api/vouchers/validate - free_shipping ONGKIRGRATIS",
            "POST",
            "/vouchers/validate",
            200,
            data={"code": "ONGKIRGRATIS", "subtotal": 200000, "shipping": 22000}
        )
        if success and response:
            if not response.get("valid"):
                self.log_fail("ONGKIRGRATIS validation", f"Expected valid=true, got {response}")
            elif response.get("discount") != 22000:
                self.log_fail("ONGKIRGRATIS discount", f"Expected discount=22000 (shipping), got {response.get('discount')}")
            else:
                print(f"   ✓ Free shipping: valid=true, discount={response.get('discount')}")

        # Test 5: Free shipping below min_spend
        success, response = self.run_test(
            "POST /api/vouchers/validate - ONGKIRGRATIS below min_spend",
            "POST",
            "/vouchers/validate",
            200,
            data={"code": "ONGKIRGRATIS", "subtotal": 100000, "shipping": 22000}
        )
        if success and response:
            if response.get("valid"):
                self.log_fail("ONGKIRGRATIS below min_spend", f"Expected valid=false, got {response}")
            else:
                print(f"   ✓ Below min_spend: valid=false, reason={response.get('reason')}")

        # Test 6: Scoped voucher AMBEROUD15 (category=amber, 15%)
        success, response = self.run_test(
            "POST /api/vouchers/validate - scoped voucher AMBEROUD15 with amber item",
            "POST",
            "/vouchers/validate",
            200,
            data={
                "code": "AMBEROUD15",
                "subtotal": 685000,
                "items": [
                    {
                        "product_id": "x",
                        "category": "amber",
                        "unit_price": 685000,
                        "quantity": 1
                    }
                ]
            }
        )
        if success and response:
            if not response.get("valid"):
                self.log_fail("AMBEROUD15 with amber", f"Expected valid=true, got {response}")
            elif response.get("discount") != 102750:
                self.log_fail("AMBEROUD15 discount", f"Expected discount=102750 (15% of 685000), got {response.get('discount')}")
            else:
                print(f"   ✓ Scoped voucher with matching category: valid=true, discount={response.get('discount')}")

        # Test 7: Scoped voucher with non-amber items
        success, response = self.run_test(
            "POST /api/vouchers/validate - AMBEROUD15 with non-amber item",
            "POST",
            "/vouchers/validate",
            200,
            data={
                "code": "AMBEROUD15",
                "subtotal": 685000,
                "items": [
                    {
                        "product_id": "y",
                        "category": "floral",
                        "unit_price": 685000,
                        "quantity": 1
                    }
                ]
            }
        )
        if success and response:
            if response.get("valid"):
                self.log_fail("AMBEROUD15 with non-amber", f"Expected valid=false, got {response}")
            else:
                print(f"   ✓ Scoped voucher with non-matching category: valid=false, reason={response.get('reason')}")

        # Test 8: Expired voucher EXPIRED2024
        success, response = self.run_test(
            "POST /api/vouchers/validate - expired voucher EXPIRED2024",
            "POST",
            "/vouchers/validate",
            200,
            data={"code": "EXPIRED2024", "subtotal": 250000}
        )
        if success and response:
            if response.get("valid"):
                self.log_fail("EXPIRED2024", f"Expected valid=false, got {response}")
            elif not response.get("reason") or "kedaluwarsa" not in response.get("reason", "").lower():
                self.log_fail("EXPIRED2024 reason", f"Expected reason containing 'kedaluwarsa', got {response.get('reason')}")
            else:
                print(f"   ✓ Expired voucher: valid=false, reason={response.get('reason')}")

        # Test 9: Unknown voucher code
        success, response = self.run_test(
            "POST /api/vouchers/validate - unknown code NOTREAL",
            "POST",
            "/vouchers/validate",
            200,
            data={"code": "NOTREAL", "subtotal": 1000}
        )
        if success and response:
            if response.get("valid"):
                self.log_fail("Unknown code", f"Expected valid=false, got {response}")
            elif not response.get("reason"):
                self.log_fail("Unknown code reason", f"Expected reason for invalid voucher, got {response}")
            else:
                print(f"   ✓ Unknown code: valid=false, reason={response.get('reason')}")

        # Test 10-15: Adversarial payloads (must NOT return 5xx)
        print("\n   Testing adversarial payloads (must not return 5xx)...")
        
        adversarial_tests = [
            ("Invalid type - code as number", {"code": 12345, "subtotal": "abc"}),
            ("Empty payload", {}),
            ("Null code", {"code": None, "subtotal": 1000}),
            ("SQL injection attempt", {"code": "'; DROP TABLE--", "subtotal": -999}),
            ("Extremely long code", {"code": "X" * 500, "subtotal": 1000000000000}),
            ("Negative subtotal", {"code": "WELCOME10", "subtotal": -50000}),
        ]
        
        for test_name, payload in adversarial_tests:
            try:
                url = f"{BASE_URL}/vouchers/validate"
                response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
                self.tests_run += 1
                
                if response.status_code >= 500:
                    self.log_fail(f"Adversarial: {test_name}", f"Got 5xx error: {response.status_code}")
                elif response.status_code in [200, 422]:
                    self.log_pass(f"Adversarial: {test_name}")
                    print(f"   ✓ {test_name}: status={response.status_code} (no 5xx)")
                else:
                    self.log_pass(f"Adversarial: {test_name}")
                    print(f"   ✓ {test_name}: status={response.status_code} (acceptable)")
            except Exception as e:
                self.log_fail(f"Adversarial: {test_name}", f"Exception: {str(e)}")

    def test_vouchers_list(self):
        """Test GET /api/vouchers"""
        print("\n" + "="*60)
        print("TESTING VOUCHER LIST (Epic E2)")
        print("="*60)

        success, response = self.run_test(
            "GET /api/vouchers returns active vouchers",
            "GET",
            "/vouchers",
            200
        )
        
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Vouchers list type", f"Expected array, got {type(response)}")
            else:
                print(f"   ✓ Returned {len(response)} vouchers")
                
                # Check that EXPIRED2024 is NOT in the list
                expired_found = any(v.get("code") == "EXPIRED2024" for v in response)
                if expired_found:
                    self.log_fail("Expired voucher in list", "EXPIRED2024 should not be in active vouchers list")
                else:
                    print("   ✓ EXPIRED2024 not in list (correct)")
                
                # Check that WELCOME10 IS in the list
                welcome_found = any(v.get("code") == "WELCOME10" for v in response)
                if not welcome_found:
                    self.log_fail("WELCOME10 missing", "WELCOME10 should be in active vouchers list")
                else:
                    print("   ✓ WELCOME10 found in list (correct)")
                
                # Verify structure of first voucher
                if len(response) > 0:
                    v = response[0]
                    required_fields = ["id", "code", "type", "value", "label"]
                    missing = [f for f in required_fields if f not in v]
                    if missing:
                        self.log_fail("Voucher structure", f"Missing fields: {missing}")
                    else:
                        print("   ✓ Voucher structure valid")

    def test_config_endpoints(self):
        """Test Epic E3 config endpoints (shipping, payment, settings)"""
        print("\n" + "="*60)
        print("TESTING CONFIG ENDPOINTS (Epic E3)")
        print("="*60)

        # Test GET /api/shipping-methods
        success, response = self.run_test(
            "GET /api/shipping-methods returns non-empty array",
            "GET",
            "/shipping-methods",
            200
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Shipping methods type", f"Expected array, got {type(response)}")
            elif len(response) == 0:
                self.log_fail("Shipping methods empty", "Expected non-empty array")
            else:
                print(f"   ✓ Returned {len(response)} shipping methods")
                # Check structure
                if len(response) > 0:
                    s = response[0]
                    if not all(k in s for k in ["id", "name", "price", "active"]):
                        self.log_fail("Shipping method structure", f"Missing required fields: {s}")

        # Test GET /api/payment-methods
        success, response = self.run_test(
            "GET /api/payment-methods returns array with groups",
            "GET",
            "/payment-methods",
            200
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Payment methods type", f"Expected array, got {type(response)}")
            elif len(response) == 0:
                self.log_fail("Payment methods empty", "Expected non-empty array")
            else:
                print(f"   ✓ Returned {len(response)} payment methods")
                # Check for groups: transfer, ewallet, cod
                groups = set(p.get("group") for p in response)
                expected_groups = {"transfer", "ewallet", "cod"}
                if not expected_groups.issubset(groups):
                    self.log_fail("Payment method groups", f"Expected groups {expected_groups}, got {groups}")
                else:
                    print(f"   ✓ Found groups: {groups}")

        # Test GET /api/settings
        success, response = self.run_test(
            "GET /api/settings returns settings object",
            "GET",
            "/settings",
            200
        )
        if success and response:
            if not isinstance(response, dict):
                self.log_fail("Settings type", f"Expected object, got {type(response)}")
            else:
                print(f"   ✓ Settings: {response}")

    def test_cart_endpoints(self):
        """Test Epic E3 cart endpoints (auth required)"""
        print("\n" + "="*60)
        print("TESTING CART ENDPOINTS (Epic E3)")
        print("="*60)

        # Test GET /api/cart without auth -> 401
        success, response = self.run_test(
            "GET /api/cart without auth returns 401",
            "GET",
            "/cart",
            401
        )

        # Test PUT /api/cart without auth -> 401
        success, response = self.run_test(
            "PUT /api/cart without auth returns 401",
            "POST",
            "/cart",
            401,
            data={"items": []}
        )

        # Login as customer to test cart with auth
        login_success, login_response = self.run_test(
            "Login as customer for cart tests",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )

        if login_success and login_response and "token" in login_response:
            token = login_response["token"]
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            # Test GET /api/cart with auth
            success, response = self.run_test(
                "GET /api/cart with auth returns cart",
                "GET",
                "/cart",
                200,
                headers=headers
            )
            if success and response:
                if not isinstance(response, dict):
                    self.log_fail("Cart type", f"Expected object, got {type(response)}")
                else:
                    print(f"   ✓ Cart: {response}")

            # Test PUT /api/cart with auth (save cart)
            # First, get a product to add to cart
            prod_success, prod_response = self.run_test(
                "Get products for cart test",
                "GET",
                "/products?limit=1",
                200
            )
            if prod_success and prod_response and len(prod_response) > 0:
                product = prod_response[0]
                product_id = product.get("id")
                volume_ml = product.get("volumes", [{}])[0].get("ml", 50)

                # Use requests.put directly for PUT method
                try:
                    url = f"{BASE_URL}/cart"
                    put_response = requests.put(
                        url,
                        json={"items": [{"product_id": product_id, "volume_ml": volume_ml, "quantity": 1}]},
                        headers=headers,
                        timeout=10
                    )
                    self.tests_run += 1
                    print("\n🔍 Testing: PUT /api/cart with auth persists cart")
                    print(f"   Status: {put_response.status_code}")
                    if put_response.status_code == 200:
                        self.log_pass("PUT /api/cart with auth")
                        print(f"   ✓ Cart saved: {put_response.json()}")
                    else:
                        self.log_fail("PUT /api/cart with auth", f"Expected 200, got {put_response.status_code}")
                except Exception as e:
                    self.log_fail("PUT /api/cart with auth", f"Exception: {str(e)}")

    def test_orders_guest_checkout(self):
        """Test Epic E3 guest checkout (POST /api/orders without auth)"""
        print("\n" + "="*60)
        print("TESTING GUEST CHECKOUT (Epic E3)")
        print("="*60)

        # Get a product to order
        prod_success, prod_response = self.run_test(
            "Get product for guest order",
            "GET",
            "/products?limit=1",
            200
        )

        if not prod_success or not prod_response or len(prod_response) == 0:
            self.log_fail("Guest checkout setup", "No products available")
            return

        product = prod_response[0]
        product_id = product.get("id")
        volume_ml = product.get("volumes", [{}])[0].get("ml", 50)

        # Create guest order
        order_data = {
            "items": [{"product_id": product_id, "volume_ml": volume_ml, "quantity": 1}],
            "address": {
                "name": "Guest User",
                "phone": "081234567890",
                "street": "Jl. Test No. 123",
                "city": "Jakarta",
                "province": "DKI Jakarta",
                "postal": "12345",
                "label": "Rumah"
            },
            "shipping_id": "jne-reg",
            "payment": {"group": "transfer", "method_id": "bca"}
        }

        success, response = self.run_test(
            "POST /api/orders as guest returns 200 with order",
            "POST",
            "/orders",
            200,
            data=order_data
        )

        if success and response:
            # Check order structure
            required_fields = ["id", "code", "items", "subtotal", "discount", "shipping", "payment", 
                             "cod_fee", "total", "status", "payment_status", "address"]
            missing = [f for f in required_fields if f not in response]
            if missing:
                self.log_fail("Guest order structure", f"Missing fields: {missing}")
            else:
                code = response.get("code")
                status = response.get("status")
                payment_status = response.get("payment_status")
                total = response.get("total")
                
                print(f"   ✓ Order created: code={code}, status={status}, payment_status={payment_status}, total={total}")
                
                # Check code format CP########
                if not code or not code.startswith("CP") or len(code) != 10:
                    self.log_fail("Guest order code format", f"Expected CP######## (10 chars), got {code}")
                
                # Check status
                if status != "pending":
                    self.log_fail("Guest order status", f"Expected 'pending', got {status}")
                
                # Check payment_status
                if payment_status != "belum_bayar":
                    self.log_fail("Guest order payment_status", f"Expected 'belum_bayar', got {payment_status}")
                
                # Store order code for later tests
                self.guest_order_code = code

    def test_orders_with_voucher(self):
        """Test Epic E3 order with voucher (logged-in customer)"""
        print("\n" + "="*60)
        print("TESTING ORDER WITH VOUCHER (Epic E3)")
        print("="*60)

        # Login as customer
        login_success, login_response = self.run_test(
            "Login as customer for voucher order",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )

        if not login_success or not login_response or "token" not in login_response:
            self.log_fail("Voucher order setup", "Login failed")
            return

        token = login_response["token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Get a product
        prod_success, prod_response = self.run_test(
            "Get product for voucher order",
            "GET",
            "/products?limit=1",
            200
        )

        if not prod_success or not prod_response or len(prod_response) == 0:
            self.log_fail("Voucher order setup", "No products available")
            return

        product = prod_response[0]
        product_id = product.get("id")
        volume_ml = product.get("volumes", [{}])[0].get("ml", 50)

        # Create order with WELCOME10 voucher
        order_data = {
            "items": [{"product_id": product_id, "volume_ml": volume_ml, "quantity": 1}],
            "address": {
                "name": "Customer User",
                "phone": "081234567890",
                "street": "Jl. Test No. 123",
                "city": "Jakarta",
                "province": "DKI Jakarta",
                "postal": "12345",
                "label": "Rumah"
            },
            "shipping_id": "jne-reg",
            "payment": {"group": "transfer", "method_id": "bca"},
            "voucher_code": "WELCOME10"
        }

        success, response = self.run_test(
            "POST /api/orders with WELCOME10 voucher returns 200",
            "POST",
            "/orders",
            200,
            data=order_data,
            headers=headers
        )

        if success and response:
            voucher_code = response.get("voucher_code")
            discount = response.get("discount", 0)
            subtotal = response.get("subtotal", 0)
            
            print(f"   ✓ Order with voucher: code={response.get('code')}, voucher={voucher_code}, discount={discount}, subtotal={subtotal}")
            
            # Check voucher_code is set
            if voucher_code != "WELCOME10":
                self.log_fail("Order voucher_code", f"Expected 'WELCOME10', got {voucher_code}")
            
            # Check discount is applied (10% of subtotal)
            expected_discount = int(subtotal * 0.1)
            if discount != expected_discount:
                self.log_fail("Order discount", f"Expected {expected_discount} (10% of {subtotal}), got {discount}")
            
            # Store order code for later tests
            self.customer_order_code = response.get("code")

    def test_orders_anti_oversell(self):
        """Test Epic E3 anti-oversell (quantity > stock -> 409)"""
        print("\n" + "="*60)
        print("TESTING ANTI-OVERSELL (Epic E3)")
        print("="*60)

        # Get a product
        prod_success, prod_response = self.run_test(
            "Get product for oversell test",
            "GET",
            "/products?limit=1",
            200
        )

        if not prod_success or not prod_response or len(prod_response) == 0:
            self.log_fail("Oversell test setup", "No products available")
            return

        product = prod_response[0]
        product_id = product.get("id")
        volume_ml = product.get("volumes", [{}])[0].get("ml", 50)

        # Try to order quantity 999 (should exceed stock)
        order_data = {
            "items": [{"product_id": product_id, "volume_ml": volume_ml, "quantity": 999}],
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
            "POST /api/orders with quantity > stock returns 409",
            "POST",
            "/orders",
            409,
            data=order_data
        )

        if success and response:
            # Check response contains available count
            if "available" not in response:
                self.log_fail("Oversell response", f"Expected 'available' field in 409 response, got {response}")
            else:
                print(f"   ✓ Stock conflict: {response}")

        # Try quantity >= 1000000 (should return 422 validation error)
        order_data["items"][0]["quantity"] = 1000000
        success, response = self.run_test(
            "POST /api/orders with quantity >= 1000000 returns 422",
            "POST",
            "/orders",
            422,
            data=order_data
        )

    def test_orders_invalid_inputs(self):
        """Test Epic E3 invalid inputs (must return 400, NOT 5xx)"""
        print("\n" + "="*60)
        print("TESTING INVALID ORDER INPUTS (Epic E3)")
        print("="*60)

        # Test nonexistent product_id -> 400
        order_data = {
            "items": [{"product_id": "prd_nonexistent", "volume_ml": 50, "quantity": 1}],
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
            "POST /api/orders with nonexistent product_id returns 400",
            "POST",
            "/orders",
            400,
            data=order_data
        )

        # Test invalid shipping_id -> 400
        # Get a valid product first
        prod_success, prod_response = self.run_test(
            "Get product for invalid shipping test",
            "GET",
            "/products?limit=1",
            200
        )

        if prod_success and prod_response and len(prod_response) > 0:
            product = prod_response[0]
            order_data["items"] = [{"product_id": product.get("id"), "volume_ml": product.get("volumes", [{}])[0].get("ml", 50), "quantity": 1}]
            order_data["shipping_id"] = "invalid-shipping"

            success, response = self.run_test(
                "POST /api/orders with invalid shipping_id returns 400",
                "POST",
                "/orders",
                400,
                data=order_data
            )

    def test_orders_list_auth(self):
        """Test Epic E3 GET /api/orders (auth required, owner-scoped)"""
        print("\n" + "="*60)
        print("TESTING ORDER LIST (Epic E3)")
        print("="*60)

        # Test without auth -> 401
        success, response = self.run_test(
            "GET /api/orders without auth returns 401",
            "GET",
            "/orders",
            401
        )

        # Test with auth -> returns user's orders only
        login_success, login_response = self.run_test(
            "Login as customer for order list",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )

        if login_success and login_response and "token" in login_response:
            token = login_response["token"]
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            success, response = self.run_test(
                "GET /api/orders with auth returns array",
                "GET",
                "/orders",
                200,
                headers=headers
            )

            if success and response:
                if not isinstance(response, list):
                    self.log_fail("Orders list type", f"Expected array, got {type(response)}")
                else:
                    print(f"   ✓ Returned {len(response)} orders")

    def test_orders_get_by_code(self):
        """Test Epic E3 GET /api/orders/{code} (IDOR-safe)"""
        print("\n" + "="*60)
        print("TESTING ORDER GET BY CODE (Epic E3)")
        print("="*60)

        # Use customer order code from previous test
        if not hasattr(self, 'customer_order_code'):
            print("   ⚠️  Skipping: no customer order code available")
            return

        code = self.customer_order_code

        # Login as customer (owner)
        login_success, login_response = self.run_test(
            "Login as customer (owner)",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )

        if login_success and login_response and "token" in login_response:
            token = login_response["token"]
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            # Owner can access their order
            success, response = self.run_test(
                f"GET /api/orders/{code} by owner returns 200",
                "GET",
                f"/orders/{code}",
                200,
                headers=headers
            )

        # Login as admin (different user)
        admin_login_success, admin_login_response = self.run_test(
            "Login as admin (different user)",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )

        if admin_login_success and admin_login_response and "token" in admin_login_response:
            admin_token = admin_login_response["token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

            # Different user should get 404 (IDOR-safe)
            success, response = self.run_test(
                f"GET /api/orders/{code} by non-owner returns 404",
                "GET",
                f"/orders/{code}",
                404,
                headers=admin_headers
            )

    def test_orders_cancel(self):
        """Test Epic E3 POST /api/orders/{code}/cancel (owner-scoped, stock restored)"""
        print("\n" + "="*60)
        print("TESTING ORDER CANCEL (Epic E3)")
        print("="*60)

        # Create a new order to cancel
        login_success, login_response = self.run_test(
            "Login as customer for cancel test",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )

        if not login_success or not login_response or "token" not in login_response:
            self.log_fail("Cancel test setup", "Login failed")
            return

        token = login_response["token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Get a product
        prod_success, prod_response = self.run_test(
            "Get product for cancel test",
            "GET",
            "/products?limit=1",
            200
        )

        if not prod_success or not prod_response or len(prod_response) == 0:
            self.log_fail("Cancel test setup", "No products available")
            return

        product = prod_response[0]
        product_id = product.get("id")
        volume_ml = product.get("volumes", [{}])[0].get("ml", 50)

        # Create order
        order_data = {
            "items": [{"product_id": product_id, "volume_ml": volume_ml, "quantity": 1}],
            "address": {
                "name": "Customer User",
                "phone": "081234567890",
                "street": "Jl. Test No. 123",
                "city": "Jakarta",
                "province": "DKI Jakarta"
            },
            "shipping_id": "jne-reg",
            "payment": {"group": "transfer", "method_id": "bca"}
        }

        create_success, create_response = self.run_test(
            "Create order for cancel test",
            "POST",
            "/orders",
            200,
            data=order_data,
            headers=headers
        )

        if not create_success or not create_response:
            self.log_fail("Cancel test setup", "Order creation failed")
            return

        order_code = create_response.get("code")
        print(f"   ✓ Created order {order_code} for cancel test")

        # Cancel order by owner
        success, response = self.run_test(
            f"POST /api/orders/{order_code}/cancel by owner returns 200",
            "POST",
            f"/orders/{order_code}/cancel",
            200,
            headers=headers
        )

        if success and response:
            status = response.get("status")
            if status != "cancelled":
                self.log_fail("Cancel order status", f"Expected 'cancelled', got {status}")
            else:
                print(f"   ✓ Order cancelled: status={status}")

        # Try to cancel by non-owner (should return 404)
        admin_login_success, admin_login_response = self.run_test(
            "Login as admin for non-owner cancel test",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )

        if admin_login_success and admin_login_response and "token" in admin_login_response:
            admin_token = admin_login_response["token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

            # Create another order as customer
            create_success2, create_response2 = self.run_test(
                "Create another order for non-owner cancel test",
                "POST",
                "/orders",
                200,
                data=order_data,
                headers=headers
            )

            if create_success2 and create_response2:
                order_code2 = create_response2.get("code")
                
                # Try to cancel by admin (non-owner) -> 404
                success, response = self.run_test(
                    f"POST /api/orders/{order_code2}/cancel by non-owner returns 404",
                    "POST",
                    f"/orders/{order_code2}/cancel",
                    404,
                    headers=admin_headers
                )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print("\n" + "="*60)
            print("FAILED TESTS DETAILS")
            print("="*60)
            for failure in self.failures:
                print(f"\n❌ {failure['test']}")
                print(f"   {failure['reason']}")
        
        return 0 if self.tests_failed == 0 else 1


    def test_e4_account(self):
        """Epic E4 - Customer Account: profile, addresses, wishlist"""
        print("\n" + "="*60)
        print("TESTING EPIC E4 - CUSTOMER ACCOUNT")
        print("="*60)
        
        # Setup: Login as customer to get token
        print("\n--- Setup: Login as customer ---")
        success, response = self.run_test(
            "Login as customer@collectorparfum.id",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )
        if not success or not response or 'token' not in response:
            print("❌ Cannot proceed with E4 tests - login failed")
            return
        
        customer_token = response['token']
        _customer_id = response['user']['id']
        auth_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {customer_token}'
        }
        
        # Setup: Login as admin (for IDOR tests)
        print("\n--- Setup: Login as admin ---")
        success, response = self.run_test(
            "Login as admin@collectorparfum.id",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )
        if not success or not response or 'token' not in response:
            print("❌ Cannot proceed with IDOR tests - admin login failed")
            admin_token = None
        else:
            admin_token = response['token']
        
        admin_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {admin_token}'
        } if admin_token else None
        
        # Test 1: Profile update
        print("\n--- Test 1: Profile Update ---")
        success, response = self.run_test(
            "PUT /api/account/profile with auth - update name and phone",
            "PUT",
            "/account/profile",
            200,
            data={"name": "Customer Updated", "phone": "081234567890"},
            headers=auth_headers
        )
        if success and response:
            if 'password_hash' in response:
                self.log_fail("PUT /api/account/profile - password_hash leak", "Response contains password_hash field")
            elif response.get('name') != "Customer Updated":
                self.log_fail("PUT /api/account/profile - name not updated", f"Expected 'Customer Updated', got '{response.get('name')}'")
            elif response.get('phone') != "081234567890":
                self.log_fail("PUT /api/account/profile - phone not updated", f"Expected '081234567890', got '{response.get('phone')}'")
            else:
                print(f"   ✓ Profile updated: name={response.get('name')}, phone={response.get('phone')}")
        
        # Test 2: Profile update - email immutability
        print("\n--- Test 2: Email Immutability ---")
        success, response = self.run_test(
            "PUT /api/account/profile - email should NOT change even if sent",
            "PUT",
            "/account/profile",
            200,
            data={"name": "Customer Test", "email": "newemail@test.com"},
            headers=auth_headers
        )
        if success and response:
            if response.get('email') != "customer@collectorparfum.id":
                self.log_fail("PUT /api/account/profile - email changed", f"Email should remain customer@collectorparfum.id, got {response.get('email')}")
            else:
                print(f"   ✓ Email immutable: {response.get('email')}")
        
        # Test 3: Profile update without auth
        print("\n--- Test 3: Profile Update Without Auth ---")
        self.run_test(
            "PUT /api/account/profile without auth - should return 401",
            "PUT",
            "/account/profile",
            401,
            data={"name": "Test"}
        )
        
        # Test 4: Addresses - Create first address (auto default)
        print("\n--- Test 4: Create First Address (Auto Default) ---")
        success, response = self.run_test(
            "POST /api/addresses - first address auto becomes default",
            "POST",
            "/addresses",
            200,
            data={
                "name": "John Doe",
                "phone": "081234567890",
                "street": "Jl. Test No. 123",
                "city": "Jakarta",
                "province": "DKI Jakarta",
                "postal": "12345",
                "label": "Rumah"
            },
            headers=auth_headers
        )
        first_addr_id = None
        if success and response:
            first_addr_id = response.get('id')
            if not response.get('is_default'):
                self.log_fail("POST /api/addresses - first address not default", f"Expected is_default=true, got {response.get('is_default')}")
            else:
                print(f"   ✓ First address is default: {first_addr_id}")
        
        # Test 5: Create second address with is_default=true (should move default)
        print("\n--- Test 5: Create Second Address as Default ---")
        success, response = self.run_test(
            "POST /api/addresses - second with is_default=true moves default",
            "POST",
            "/addresses",
            200,
            data={
                "name": "Jane Doe",
                "phone": "082345678901",
                "street": "Jl. Test 2 No. 456",
                "city": "Bandung",
                "province": "Jawa Barat",
                "postal": "40123",
                "label": "Kantor",
                "is_default": True
            },
            headers=auth_headers
        )
        second_addr_id = None
        if success and response:
            second_addr_id = response.get('id')
            if not response.get('is_default'):
                self.log_fail("POST /api/addresses - second address not default", f"Expected is_default=true, got {response.get('is_default')}")
            else:
                print(f"   ✓ Second address is default: {second_addr_id}")
        
        # Test 6: Verify only one default (list addresses)
        print("\n--- Test 6: Verify Single Default Invariant ---")
        success, response = self.run_test(
            "GET /api/addresses - verify only one default",
            "GET",
            "/addresses",
            200,
            headers=auth_headers
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("GET /api/addresses - not a list", f"Expected list, got {type(response)}")
            else:
                default_count = sum(1 for addr in response if addr.get('is_default'))
                if default_count != 1:
                    self.log_fail("GET /api/addresses - multiple defaults", f"Expected 1 default, found {default_count}")
                else:
                    print(f"   ✓ Single default invariant maintained: {default_count} default address")
                    print(f"   ✓ Total addresses: {len(response)}")
        
        # Test 7: Set default via POST /api/addresses/{id}/default
        print("\n--- Test 7: Set Default Address ---")
        if first_addr_id:
            success, response = self.run_test(
                f"POST /api/addresses/{first_addr_id}/default - set first as default",
                "POST",
                f"/addresses/{first_addr_id}/default",
                200,
                headers=auth_headers
            )
            if success and response:
                if not isinstance(response, list):
                    self.log_fail("POST /api/addresses/{id}/default - not a list", f"Expected list, got {type(response)}")
                else:
                    default_count = sum(1 for addr in response if addr.get('is_default'))
                    default_addr = next((addr for addr in response if addr.get('is_default')), None)
                    if default_count != 1:
                        self.log_fail("POST /api/addresses/{id}/default - multiple defaults", f"Expected 1 default, found {default_count}")
                    elif default_addr and default_addr.get('id') != first_addr_id:
                        self.log_fail("POST /api/addresses/{id}/default - wrong default", f"Expected {first_addr_id} as default, got {default_addr.get('id')}")
                    else:
                        print(f"   ✓ Default moved to first address: {first_addr_id}")
        
        # Test 8: Update address
        print("\n--- Test 8: Update Address ---")
        if second_addr_id:
            success, response = self.run_test(
                f"PUT /api/addresses/{second_addr_id} - update address",
                "PUT",
                f"/addresses/{second_addr_id}",
                200,
                data={
                    "name": "Jane Doe Updated",
                    "phone": "082345678901",
                    "street": "Jl. Updated No. 789",
                    "city": "Bandung",
                    "province": "Jawa Barat",
                    "postal": "40123",
                    "label": "Kantor"
                },
                headers=auth_headers
            )
            if success and response:
                if response.get('name') != "Jane Doe Updated":
                    self.log_fail("PUT /api/addresses/{id} - name not updated", f"Expected 'Jane Doe Updated', got '{response.get('name')}'")
                elif response.get('street') != "Jl. Updated No. 789":
                    self.log_fail("PUT /api/addresses/{id} - street not updated", f"Expected 'Jl. Updated No. 789', got '{response.get('street')}'")
                else:
                    print(f"   ✓ Address updated: {response.get('name')}, {response.get('street')}")
        
        # Test 9: Address IDOR - admin tries to update customer's address
        print("\n--- Test 9: Address IDOR Protection (PUT) ---")
        if admin_headers and second_addr_id:
            success, response = self.run_test(
                f"PUT /api/addresses/{second_addr_id} as admin - should return 404",
                "PUT",
                f"/addresses/{second_addr_id}",
                404,
                data={
                    "name": "Hacker",
                    "phone": "999",
                    "street": "Hacked",
                    "city": "Hacked",
                    "province": "Hacked"
                },
                headers=admin_headers
            )
            if success:
                print("   ✓ IDOR protection working: admin cannot update customer's address")
        
        # Test 10: Address IDOR - admin tries to delete customer's address
        print("\n--- Test 10: Address IDOR Protection (DELETE) ---")
        if admin_headers and second_addr_id:
            success, response = self.run_test(
                f"DELETE /api/addresses/{second_addr_id} as admin - should return 404",
                "DELETE",
                f"/addresses/{second_addr_id}",
                404,
                headers=admin_headers
            )
            if success:
                print("   ✓ IDOR protection working: admin cannot delete customer's address")
        
        # Test 11: Delete address (and verify default promotion)
        print("\n--- Test 11: Delete Address ---")
        if second_addr_id:
            success, response = self.run_test(
                f"DELETE /api/addresses/{second_addr_id} - delete address",
                "DELETE",
                f"/addresses/{second_addr_id}",
                200,
                headers=auth_headers
            )
            if success and response:
                if not response.get('ok'):
                    self.log_fail("DELETE /api/addresses/{id} - not ok", f"Expected ok=true, got {response}")
                else:
                    print(f"   ✓ Address deleted: {second_addr_id}")
                    
                    # Verify remaining address is now default
                    success2, response2 = self.run_test(
                        "GET /api/addresses - verify default promotion after delete",
                        "GET",
                        "/addresses",
                        200,
                        headers=auth_headers
                    )
                    if success2 and response2:
                        default_count = sum(1 for addr in response2 if addr.get('is_default'))
                        if default_count != 1:
                            self.log_fail("DELETE address - default not promoted", f"Expected 1 default after delete, found {default_count}")
                        else:
                            print(f"   ✓ Default promoted after delete: {default_count} default address")
        
        # Test 12: Wishlist - GET (auth required)
        print("\n--- Test 12: Wishlist GET ---")
        success, response = self.run_test(
            "GET /api/wishlist with auth - returns {product_ids:[...]}",
            "GET",
            "/wishlist",
            200,
            headers=auth_headers
        )
        if success and response:
            if 'product_ids' not in response:
                self.log_fail("GET /api/wishlist - missing product_ids", f"Expected {{product_ids:[...]}}, got {response}")
            elif not isinstance(response['product_ids'], list):
                self.log_fail("GET /api/wishlist - product_ids not list", f"Expected list, got {type(response['product_ids'])}")
            else:
                print(f"   ✓ Wishlist returned: {len(response['product_ids'])} items")
        
        # Test 13: Wishlist without auth
        print("\n--- Test 13: Wishlist Without Auth ---")
        self.run_test(
            "GET /api/wishlist without auth - should return 401",
            "GET",
            "/wishlist",
            401
        )
        
        # Test 14: Wishlist toggle - add product
        print("\n--- Test 14: Wishlist Toggle (Add) ---")
        # First, get a valid product ID
        success, products = self.run_test(
            "GET /api/products - get valid product for wishlist",
            "GET",
            "/products?limit=1",
            200
        )
        test_product_id = None
        if success and products and isinstance(products, list) and len(products) > 0:
            test_product_id = products[0].get('id')
            print(f"   Using product ID: {test_product_id}")
        
        if test_product_id:
            success, response = self.run_test(
                f"POST /api/wishlist/toggle - add product {test_product_id}",
                "POST",
                "/wishlist/toggle",
                200,
                data={"product_id": test_product_id},
                headers=auth_headers
            )
            if success and response:
                if 'product_ids' not in response:
                    self.log_fail("POST /api/wishlist/toggle - missing product_ids", f"Expected {{product_ids:[...]}}, got {response}")
                elif test_product_id not in response['product_ids']:
                    self.log_fail("POST /api/wishlist/toggle - product not added", f"Expected {test_product_id} in wishlist, got {response['product_ids']}")
                else:
                    print(f"   ✓ Product added to wishlist: {test_product_id}")
            
            # Test 15: Wishlist toggle - remove product
            print("\n--- Test 15: Wishlist Toggle (Remove) ---")
            success, response = self.run_test(
                f"POST /api/wishlist/toggle - remove product {test_product_id}",
                "POST",
                "/wishlist/toggle",
                200,
                data={"product_id": test_product_id},
                headers=auth_headers
            )
            if success and response:
                if 'product_ids' not in response:
                    self.log_fail("POST /api/wishlist/toggle - missing product_ids", f"Expected {{product_ids:[...]}}, got {response}")
                elif test_product_id in response['product_ids']:
                    self.log_fail("POST /api/wishlist/toggle - product not removed", f"Expected {test_product_id} removed from wishlist, still present")
                else:
                    print(f"   ✓ Product removed from wishlist: {test_product_id}")
        
        # Test 16: Wishlist toggle - nonexistent product
        print("\n--- Test 16: Wishlist Toggle (Invalid Product) ---")
        self.run_test(
            "POST /api/wishlist/toggle - nonexistent product should return 400",
            "POST",
            "/wishlist/toggle",
            400,
            data={"product_id": "prd_ghost"},
            headers=auth_headers
        )
        
        # Test 17: Wishlist merge
        print("\n--- Test 17: Wishlist Merge ---")
        if test_product_id:
            # Get another product ID
            success, products = self.run_test(
                "GET /api/products - get second product for merge",
                "GET",
                "/products?limit=2&offset=1",
                200
            )
            test_product_id_2 = None
            if success and products and isinstance(products, list) and len(products) > 0:
                test_product_id_2 = products[0].get('id')
                print(f"   Using second product ID: {test_product_id_2}")
            
            merge_ids = [test_product_id]
            if test_product_id_2:
                merge_ids.append(test_product_id_2)
            
            success, response = self.run_test(
                f"POST /api/wishlist/merge - merge {len(merge_ids)} products",
                "POST",
                "/wishlist/merge",
                200,
                data={"product_ids": merge_ids},
                headers=auth_headers
            )
            if success and response:
                if 'product_ids' not in response:
                    self.log_fail("POST /api/wishlist/merge - missing product_ids", f"Expected {{product_ids:[...]}}, got {response}")
                elif not all(pid in response['product_ids'] for pid in merge_ids):
                    self.log_fail("POST /api/wishlist/merge - not all products merged", f"Expected {merge_ids} in wishlist, got {response['product_ids']}")
                else:
                    print(f"   ✓ Products merged: {len(response['product_ids'])} items in wishlist")
                    
                    # Verify deduplication
                    if len(response['product_ids']) != len(set(response['product_ids'])):
                        self.log_fail("POST /api/wishlist/merge - duplicates found", f"Wishlist has duplicates: {response['product_ids']}")
                    else:
                        print("   ✓ No duplicates in wishlist")
        
        # Test 18: Wishlist merge with invalid IDs (should drop them)
        print("\n--- Test 18: Wishlist Merge (Invalid IDs Dropped) ---")
        success, response = self.run_test(
            "POST /api/wishlist/merge - invalid IDs should be dropped",
            "POST",
            "/wishlist/merge",
            200,
            data={"product_ids": ["prd_invalid1", "prd_invalid2"]},
            headers=auth_headers
        )
        if success and response:
            if 'product_ids' not in response:
                self.log_fail("POST /api/wishlist/merge - missing product_ids", f"Expected {{product_ids:[...]}}, got {response}")
            elif "prd_invalid1" in response['product_ids'] or "prd_invalid2" in response['product_ids']:
                self.log_fail("POST /api/wishlist/merge - invalid IDs not dropped", f"Invalid IDs should be dropped, got {response['product_ids']}")
            else:
                print("   ✓ Invalid IDs dropped from wishlist")
        
        # Test 19: Malformed requests (should not return 5xx)
        print("\n--- Test 19: Malformed Requests (No 5xx) ---")
        
        # Empty body for profile update
        url = f"{BASE_URL}/account/profile"
        try:
            resp = requests.put(url, json={}, headers=auth_headers, timeout=10)
            self.tests_run += 1
            if resp.status_code >= 500:
                self.log_fail("PUT /api/account/profile empty body - returns 5xx", f"Got {resp.status_code}, should be 400/422")
            else:
                self.log_pass(f"PUT /api/account/profile empty body - returns {resp.status_code} (not 5xx)")
        except Exception as e:
            self.tests_run += 1
            self.log_fail("PUT /api/account/profile empty body", str(e))
        
        # Malformed address
        url = f"{BASE_URL}/addresses"
        try:
            resp = requests.post(url, json={"name": "Test"}, headers=auth_headers, timeout=10)
            self.tests_run += 1
            if resp.status_code >= 500:
                self.log_fail("POST /api/addresses malformed - returns 5xx", f"Got {resp.status_code}, should be 400/422")
            else:
                self.log_pass(f"POST /api/addresses malformed - returns {resp.status_code} (not 5xx)")
        except Exception as e:
            self.tests_run += 1
            self.log_fail("POST /api/addresses malformed", str(e))
        
        # Malformed wishlist toggle
        url = f"{BASE_URL}/wishlist/toggle"
        try:
            resp = requests.post(url, json={}, headers=auth_headers, timeout=10)
            self.tests_run += 1
            if resp.status_code >= 500:
                self.log_fail("POST /api/wishlist/toggle empty - returns 5xx", f"Got {resp.status_code}, should be 400/422")
            else:
                self.log_pass(f"POST /api/wishlist/toggle empty - returns {resp.status_code} (not 5xx)")
        except Exception as e:
            self.tests_run += 1
            self.log_fail("POST /api/wishlist/toggle empty", str(e))
        
        print("\n" + "="*60)
        print("EPIC E4 TESTS COMPLETED")
        print("="*60)


    def test_e7_analytics_event(self):
        """Test E7 - Analytics event endpoint"""
        print("\n" + "="*60)
        print("TESTING E7 - ANALYTICS EVENT")
        print("="*60)
        
        # Test valid event (page_view)
        success, response = self.run_test(
            "POST /api/analytics/event with valid page_view",
            "POST",
            "/analytics/event",
            200,
            data={
                "type": "page_view",
                "path": "/",
                "session_hint": "test_session",
                "meta": {"test": "value"}
            }
        )
        if success and response:
            if not response.get("ok"):
                self.log_fail("Analytics event response", f"Expected ok:true, got: {response}")
            if not response.get("stored"):
                self.log_fail("Analytics event stored", f"Expected stored:true, got: {response}")
        
        # Test unknown event type (should return 200 with stored:false, NOT 5xx)
        success, response = self.run_test(
            "POST /api/analytics/event with unknown type returns 200 stored:false",
            "POST",
            "/analytics/event",
            200,
            data={
                "type": "unknown_type_xyz",
                "path": "/test"
            }
        )
        if success and response:
            if response.get("stored") is not False:
                self.log_fail("Analytics unknown type", f"Expected stored:false, got: {response}")
        
        # Test PII scrub - email and phone should be removed
        success, response = self.run_test(
            "POST /api/analytics/event with PII (should be scrubbed)",
            "POST",
            "/analytics/event",
            200,
            data={
                "type": "search",
                "path": "/shop",
                "meta": {
                    "email": "leak@test.com",
                    "phone": "081234567890",
                    "safe_field": "safe_value",
                    "count": 5
                }
            }
        )
        if success and response:
            if not response.get("ok"):
                self.log_fail("Analytics PII scrub response", f"Expected ok:true, got: {response}")
        
        # Test empty/malformed input (should not cause 5xx)
        url = f"{BASE_URL}/analytics/event"
        try:
            resp = requests.post(url, json={}, headers={'Content-Type': 'application/json'}, timeout=10)
            self.tests_run += 1
            if resp.status_code >= 500:
                self.log_fail("POST /api/analytics/event empty - returns 5xx", f"Got {resp.status_code}, should not be 5xx")
            else:
                self.log_pass(f"POST /api/analytics/event empty - returns {resp.status_code} (not 5xx)")
        except Exception as e:
            self.tests_run += 1
            self.log_fail("POST /api/analytics/event empty", str(e))

    def test_e7_sitemap(self):
        """Test E7 - Sitemap XML"""
        print("\n" + "="*60)
        print("TESTING E7 - SITEMAP XML")
        print("="*60)
        
        url = f"{BASE_URL}/sitemap.xml"
        try:
            resp = requests.get(url, timeout=10)
            self.tests_run += 1
            
            if resp.status_code != 200:
                self.log_fail("GET /api/sitemap.xml", f"Expected 200, got {resp.status_code}")
            else:
                # Check content-type
                content_type = resp.headers.get('content-type', '')
                if 'application/xml' not in content_type:
                    self.log_fail("Sitemap content-type", f"Expected application/xml, got: {content_type}")
                else:
                    self.log_pass("GET /api/sitemap.xml returns 200 with application/xml")
                
                # Check XML structure
                body = resp.text
                if '<urlset' not in body or '</urlset>' not in body:
                    self.log_fail("Sitemap XML structure", "Missing <urlset> tags")
                else:
                    self.log_pass("Sitemap contains valid XML structure")
                
                # Check for product URLs (should contain /parfum/)
                if '/parfum/' in body:
                    self.log_pass("Sitemap contains product URLs")
                else:
                    print("   ⚠️  WARNING: Sitemap doesn't contain product URLs (/parfum/)")
                
                # Check for category URLs (should contain ?cat=)
                if '?cat=' in body or '/shop' in body:
                    self.log_pass("Sitemap contains shop/category URLs")
                else:
                    print("   ⚠️  WARNING: Sitemap doesn't contain category URLs")
        
        except Exception as e:
            self.tests_run += 1
            self.log_fail("GET /api/sitemap.xml", str(e))

    def test_e7_settings_growth_fields(self):
        """Test E7 - Settings endpoint includes growth fields"""
        print("\n" + "="*60)
        print("TESTING E7 - SETTINGS GROWTH FIELDS")
        print("="*60)
        
        success, response = self.run_test(
            "GET /api/settings includes growth fields",
            "GET",
            "/settings",
            200
        )
        
        if success and response:
            required_fields = [
                "whatsapp_number",
                "seo_title",
                "seo_description",
                "og_image",
                "social_instagram",
                "social_facebook",
                "social_tiktok",
                "ga_measurement_id",
                "site_url"
            ]
            
            missing_fields = [f for f in required_fields if f not in response]
            
            if missing_fields:
                self.log_fail("Settings growth fields", f"Missing fields: {missing_fields}")
            else:
                self.log_pass("All growth fields present in /api/settings")
                print(f"   Growth fields: whatsapp_number={response.get('whatsapp_number')}, seo_title={response.get('seo_title')}")

    def test_e7_admin_analytics(self):
        """Test E7 - Admin analytics endpoint with RBAC"""
        print("\n" + "="*60)
        print("TESTING E7 - ADMIN ANALYTICS")
        print("="*60)
        
        # Test without token (should return 401/403)
        url = f"{BASE_URL}/admin/analytics"
        try:
            resp = requests.get(url, timeout=10)
            self.tests_run += 1
            if resp.status_code in (401, 403):
                self.log_pass(f"GET /api/admin/analytics without token returns {resp.status_code}")
            else:
                self.log_fail("Admin analytics RBAC", f"Expected 401/403 without token, got {resp.status_code}")
        except Exception as e:
            self.tests_run += 1
            self.log_fail("GET /api/admin/analytics without token", str(e))
        
        # Login as admin
        admin_success, admin_response = self.run_test(
            "Admin login for analytics test",
            "POST",
            "/auth/login",
            200,
            data={
                "email": "admin@collectorparfum.id",
                "password": "Admin#2026"
            }
        )
        
        if admin_success and admin_response and admin_response.get("token"):
            admin_token = admin_response["token"]
            admin_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {admin_token}'
            }
            
            # Test with admin token
            success, response = self.run_test(
                "GET /api/admin/analytics with admin token",
                "GET",
                "/admin/analytics?range=30",
                200,
                headers=admin_headers
            )
            
            if success and response:
                # Check response structure
                required_keys = ["funnel", "totals", "conversion_rate", "top_products"]
                missing_keys = [k for k in required_keys if k not in response]
                
                if missing_keys:
                    self.log_fail("Admin analytics response structure", f"Missing keys: {missing_keys}")
                else:
                    self.log_pass("Admin analytics response has all required keys")
                
                # Check funnel structure
                funnel = response.get("funnel", [])
                if not isinstance(funnel, list):
                    self.log_fail("Admin analytics funnel", f"Expected list, got {type(funnel)}")
                else:
                    expected_steps = ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"]
                    funnel_steps = [f.get("step") for f in funnel]
                    if funnel_steps == expected_steps:
                        self.log_pass("Admin analytics funnel has correct 5 steps")
                    else:
                        self.log_fail("Admin analytics funnel steps", f"Expected {expected_steps}, got {funnel_steps}")
                
                # Check totals
                totals = response.get("totals", {})
                if "events" in totals and "orders" in totals:
                    self.log_pass("Admin analytics totals structure correct")
                else:
                    self.log_fail("Admin analytics totals", f"Missing events or orders in totals: {totals}")
        
        # Test with customer token (should return 403)
        customer_success, customer_response = self.run_test(
            "Customer login for analytics RBAC test",
            "POST",
            "/auth/login",
            200,
            data={
                "email": "customer@collectorparfum.id",
                "password": "Customer#2026"
            }
        )
        
        if customer_success and customer_response and customer_response.get("token"):
            customer_token = customer_response["token"]
            customer_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {customer_token}'
            }
            
            try:
                resp = requests.get(f"{BASE_URL}/admin/analytics", headers=customer_headers, timeout=10)
                self.tests_run += 1
                if resp.status_code == 403:
                    self.log_pass("GET /api/admin/analytics with customer token returns 403")
                else:
                    self.log_fail("Admin analytics customer RBAC", f"Expected 403 with customer token, got {resp.status_code}")
            except Exception as e:
                self.tests_run += 1
                self.log_fail("GET /api/admin/analytics with customer token", str(e))

    def test_e7_admin_crm(self):
        """Test E7 - Admin CRM segments endpoint with RBAC"""
        print("\n" + "="*60)
        print("TESTING E7 - ADMIN CRM SEGMENTS")
        print("="*60)
        
        # Test without token (should return 401/403)
        url = f"{BASE_URL}/admin/crm/segments"
        try:
            resp = requests.get(url, timeout=10)
            self.tests_run += 1
            if resp.status_code in (401, 403):
                self.log_pass(f"GET /api/admin/crm/segments without token returns {resp.status_code}")
            else:
                self.log_fail("Admin CRM RBAC", f"Expected 401/403 without token, got {resp.status_code}")
        except Exception as e:
            self.tests_run += 1
            self.log_fail("GET /api/admin/crm/segments without token", str(e))
        
        # Login as admin
        admin_success, admin_response = self.run_test(
            "Admin login for CRM test",
            "POST",
            "/auth/login",
            200,
            data={
                "email": "admin@collectorparfum.id",
                "password": "Admin#2026"
            }
        )
        
        if admin_success and admin_response and admin_response.get("token"):
            admin_token = admin_response["token"]
            admin_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {admin_token}'
            }
            
            # Test with admin token
            success, response = self.run_test(
                "GET /api/admin/crm/segments with admin token",
                "GET",
                "/admin/crm/segments",
                200,
                headers=admin_headers
            )
            
            if success and response:
                # Check response structure
                required_keys = ["segments", "rows", "thresholds"]
                missing_keys = [k for k in required_keys if k not in response]
                
                if missing_keys:
                    self.log_fail("Admin CRM response structure", f"Missing keys: {missing_keys}")
                else:
                    self.log_pass("Admin CRM response has all required keys")
                
                # Check segments is dict
                segments = response.get("segments", {})
                if not isinstance(segments, dict):
                    self.log_fail("Admin CRM segments type", f"Expected dict, got {type(segments)}")
                else:
                    self.log_pass("Admin CRM segments is dict")
                
                # Check rows is list
                rows = response.get("rows", [])
                if not isinstance(rows, list):
                    self.log_fail("Admin CRM rows type", f"Expected list, got {type(rows)}")
                else:
                    self.log_pass("Admin CRM rows is list")
                
                # Check thresholds is dict
                thresholds = response.get("thresholds", {})
                if not isinstance(thresholds, dict):
                    self.log_fail("Admin CRM thresholds type", f"Expected dict, got {type(thresholds)}")
                else:
                    self.log_pass("Admin CRM thresholds is dict")
        
        # Test with customer token (should return 403)
        customer_success, customer_response = self.run_test(
            "Customer login for CRM RBAC test",
            "POST",
            "/auth/login",
            200,
            data={
                "email": "customer@collectorparfum.id",
                "password": "Customer#2026"
            }
        )
        
        if customer_success and customer_response and customer_response.get("token"):
            customer_token = customer_response["token"]
            customer_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {customer_token}'
            }
            
            try:
                resp = requests.get(f"{BASE_URL}/admin/crm/segments", headers=customer_headers, timeout=10)
                self.tests_run += 1
                if resp.status_code == 403:
                    self.log_pass("GET /api/admin/crm/segments with customer token returns 403")
                else:
                    self.log_fail("Admin CRM customer RBAC", f"Expected 403 with customer token, got {resp.status_code}")
            except Exception as e:
                self.tests_run += 1
                self.log_fail("GET /api/admin/crm/segments with customer token", str(e))

    def test_e7_admin_settings_growth(self):
        """Test E7 - Admin can update growth settings"""
        print("\n" + "="*60)
        print("TESTING E7 - ADMIN SETTINGS GROWTH UPDATE")
        print("="*60)
        
        # Login as admin
        admin_success, admin_response = self.run_test(
            "Admin login for settings update test",
            "POST",
            "/auth/login",
            200,
            data={
                "email": "admin@collectorparfum.id",
                "password": "Admin#2026"
            }
        )
        
        if admin_success and admin_response and admin_response.get("token"):
            admin_token = admin_response["token"]
            admin_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {admin_token}'
            }
            
            # Update growth settings
            test_wa = "6281234567890"
            test_seo = "Collector Parfum - Test SEO Title"
            test_ga = "G-TEST123"
            
            success, response = self.run_test(
                "PUT /api/admin/settings with growth fields",
                "PUT",
                "/admin/settings",
                200,
                data={
                    "whatsapp_number": test_wa,
                    "seo_title": test_seo,
                    "ga_measurement_id": test_ga,
                    "social_instagram": "https://instagram.com/test"
                },
                headers=admin_headers
            )
            
            if success and response:
                # Verify the update by reading public settings
                verify_success, verify_response = self.run_test(
                    "GET /api/settings to verify growth fields update",
                    "GET",
                    "/settings",
                    200
                )
                
                if verify_success and verify_response:
                    if verify_response.get("whatsapp_number") == test_wa:
                        self.log_pass("Growth settings whatsapp_number updated correctly")
                    else:
                        self.log_fail("Growth settings whatsapp_number", f"Expected {test_wa}, got {verify_response.get('whatsapp_number')}")
                    
                    if verify_response.get("seo_title") == test_seo:
                        self.log_pass("Growth settings seo_title updated correctly")
                    else:
                        self.log_fail("Growth settings seo_title", f"Expected {test_seo}, got {verify_response.get('seo_title')}")
                    
                    if verify_response.get("ga_measurement_id") == test_ga:
                        self.log_pass("Growth settings ga_measurement_id updated correctly")
                    else:
                        self.log_fail("Growth settings ga_measurement_id", f"Expected {test_ga}, got {verify_response.get('ga_measurement_id')}")

    def print_summary(self):  # noqa: F811
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total tests run: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        
        if self.tests_failed > 0:
            print("\n" + "="*60)
            print("FAILED TESTS:")
            print("="*60)
            for failure in self.failures:
                print(f"\n❌ {failure['test']}")
                print(f"   {failure['reason']}")
        
        print("\n" + "="*60)
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*60)
        
        return 0 if self.tests_failed == 0 else 1

    def test_e10_product_io(self):
        """Epic E10 - Product Export/Import (admin-only)"""
        print("\n" + "="*60)
        print("TESTING EPIC E10 - PRODUCT EXPORT/IMPORT")
        print("="*60)
        
        # Setup: Login as admin to get token
        print("\n--- Setup: Login as admin ---")
        success, response = self.run_test(
            "Login as admin@collectorparfum.id",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )
        if not success or not response or 'token' not in response:
            print("❌ Cannot proceed with E10 tests - admin login failed")
            return
        
        admin_token = response['token']
        admin_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {admin_token}'
        }
        
        # Test 1: GET /api/admin/products/io/export?format=csv (admin-only)
        print("\n--- Test 1: Export CSV ---")
        try:
            url = f"{BASE_URL}/admin/products/io/export?format=csv"
            resp = requests.get(url, headers=admin_headers, timeout=30)
            self.tests_run += 1
            print(f"\n🔍 Testing: GET /api/admin/products/io/export?format=csv")
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                if 'text/csv' in resp.headers.get('content-type', ''):
                    self.log_pass("Export CSV returns 200 with CSV content")
                    print(f"   Content-Type: {resp.headers.get('content-type')}")
                    print(f"   Content-Disposition: {resp.headers.get('content-disposition')}")
                else:
                    self.log_fail("Export CSV content-type", f"Expected text/csv, got {resp.headers.get('content-type')}")
            else:
                self.log_fail("Export CSV", f"Expected 200, got {resp.status_code}")
        except Exception as e:
            self.log_fail("Export CSV", f"Exception: {str(e)}")
        
        # Test 2: GET /api/admin/products/io/export?format=xlsx (admin-only)
        print("\n--- Test 2: Export XLSX ---")
        try:
            url = f"{BASE_URL}/admin/products/io/export?format=xlsx"
            resp = requests.get(url, headers=admin_headers, timeout=30)
            self.tests_run += 1
            print(f"\n🔍 Testing: GET /api/admin/products/io/export?format=xlsx")
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                if 'spreadsheetml' in resp.headers.get('content-type', ''):
                    self.log_pass("Export XLSX returns 200 with XLSX content")
                    print(f"   Content-Type: {resp.headers.get('content-type')}")
                else:
                    self.log_fail("Export XLSX content-type", f"Expected XLSX mime, got {resp.headers.get('content-type')}")
            else:
                self.log_fail("Export XLSX", f"Expected 200, got {resp.status_code}")
        except Exception as e:
            self.log_fail("Export XLSX", f"Exception: {str(e)}")
        
        # Test 3: GET /api/admin/products/io/template?format=csv
        print("\n--- Test 3: Template CSV ---")
        try:
            url = f"{BASE_URL}/admin/products/io/template?format=csv"
            resp = requests.get(url, headers=admin_headers, timeout=30)
            self.tests_run += 1
            print(f"\n🔍 Testing: GET /api/admin/products/io/template?format=csv")
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                self.log_pass("Template CSV returns 200")
            else:
                self.log_fail("Template CSV", f"Expected 200, got {resp.status_code}")
        except Exception as e:
            self.log_fail("Template CSV", f"Exception: {str(e)}")
        
        # Test 4: GET /api/admin/products/io/template?format=xlsx
        print("\n--- Test 4: Template XLSX ---")
        try:
            url = f"{BASE_URL}/admin/products/io/template?format=xlsx"
            resp = requests.get(url, headers=admin_headers, timeout=30)
            self.tests_run += 1
            print(f"\n🔍 Testing: GET /api/admin/products/io/template?format=xlsx")
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                self.log_pass("Template XLSX returns 200")
            else:
                self.log_fail("Template XLSX", f"Expected 200, got {resp.status_code}")
        except Exception as e:
            self.log_fail("Template XLSX", f"Exception: {str(e)}")
        
        # Test 5: POST /api/admin/products/io/analyze (with CSV data)
        print("\n--- Test 5: Analyze CSV ---")
        try:
            import io
            csv_content = "Nama Produk,Kategori,Ukuran (ml),Harga\nTest Product,amber,50,100000"
            files = {'file': ('test.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')}
            url = f"{BASE_URL}/admin/products/io/analyze"
            resp = requests.post(url, files=files, headers={'Authorization': f'Bearer {admin_token}'}, timeout=30)
            self.tests_run += 1
            print(f"\n🔍 Testing: POST /api/admin/products/io/analyze")
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if 'headers' in data and 'rows' in data and 'suggested_mapping' in data:
                    self.log_pass("Analyze CSV returns 200 with correct structure")
                    print(f"   Headers: {data.get('headers')}")
                    print(f"   Rows: {len(data.get('rows', []))}")
                else:
                    self.log_fail("Analyze CSV structure", f"Missing required fields: {data}")
            else:
                self.log_fail("Analyze CSV", f"Expected 200, got {resp.status_code}")
        except Exception as e:
            self.log_fail("Analyze CSV", f"Exception: {str(e)}")
        
        # Test 6: POST /api/admin/products/io/validate
        print("\n--- Test 6: Validate Import ---")
        success, response = self.run_test(
            "POST /api/admin/products/io/validate with valid data",
            "POST",
            "/admin/products/io/validate",
            200,
            data={
                "rows": [{"Nama Produk": "Test", "Kategori": "amber", "Ukuran (ml)": "50", "Harga": "100000"}],
                "mapping": {"name": "Nama Produk", "category": "Kategori", "variant_ml": "Ukuran (ml)", "variant_price": "Harga"}
            },
            headers=admin_headers
        )
        if success and response:
            if 'products' in response and 'reports' in response and 'summary' in response:
                print(f"   ✓ Validate structure correct: {response.get('summary')}")
            else:
                self.log_fail("Validate structure", f"Missing required fields: {response}")
        
        # Test 7: POST /api/admin/products/io/commit (add-only mode)
        print("\n--- Test 7: Commit Import (add-only) ---")
        success, response = self.run_test(
            "POST /api/admin/products/io/commit with add-only mode",
            "POST",
            "/admin/products/io/commit",
            200,
            data={
                "rows": [{"Nama Produk": f"Test Import {datetime.now().strftime('%H%M%S')}", "Kategori": "amber", "Ukuran (ml)": "50", "Harga": "100000"}],
                "mapping": {"name": "Nama Produk", "category": "Kategori", "variant_ml": "Ukuran (ml)", "variant_price": "Harga"},
                "mode": "add-only"
            },
            headers=admin_headers
        )
        if success and response:
            if 'created' in response and 'updated' in response:
                print(f"   ✓ Commit result: created={response.get('created')}, updated={response.get('updated')}")
            else:
                self.log_fail("Commit structure", f"Missing required fields: {response}")
        
        # Test 8: RBAC - non-admin cannot access export
        print("\n--- Test 8: RBAC - Export requires admin ---")
        # Login as customer
        cust_success, cust_response = self.run_test(
            "Login as customer for RBAC test",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )
        if cust_success and cust_response and 'token' in cust_response:
            customer_token = cust_response['token']
            customer_headers = {'Authorization': f'Bearer {customer_token}'}
            
            try:
                url = f"{BASE_URL}/admin/products/io/export?format=csv"
                resp = requests.get(url, headers=customer_headers, timeout=10)
                self.tests_run += 1
                print(f"\n🔍 Testing: Export as non-admin returns 401/403")
                print(f"   Status: {resp.status_code}")
                if resp.status_code in [401, 403]:
                    self.log_pass("RBAC - Export requires admin (401/403)")
                else:
                    self.log_fail("RBAC - Export", f"Expected 401/403, got {resp.status_code}")
            except Exception as e:
                self.log_fail("RBAC - Export", f"Exception: {str(e)}")
        
        # Test 9: Unauthenticated access
        print("\n--- Test 9: RBAC - Unauthenticated access ---")
        try:
            url = f"{BASE_URL}/admin/products/io/export?format=csv"
            resp = requests.get(url, timeout=10)
            self.tests_run += 1
            print(f"\n🔍 Testing: Export without auth returns 401")
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 401:
                self.log_pass("RBAC - Export requires auth (401)")
            else:
                self.log_fail("RBAC - Export no auth", f"Expected 401, got {resp.status_code}")
        except Exception as e:
            self.log_fail("RBAC - Export no auth", f"Exception: {str(e)}")

    def test_store_locations_and_reviews(self):
        """Test store locations and Google Reviews feature (Epic E11)"""
        print("\n" + "="*60)
        print("TESTING STORE LOCATIONS & GOOGLE REVIEWS (Epic E11)")
        print("="*60)
        
        # Test 1: GET /api/stores (public, should return locations + config)
        print("\n--- Test 1: GET /api/stores (public) ---")
        success, response = self.run_test(
            "GET /api/stores returns locations and config",
            "GET",
            "/stores",
            200
        )
        if success and response:
            if 'locations' in response and 'config' in response:
                locations = response['locations']
                config = response['config']
                print(f"   ✓ Found {len(locations)} locations")
                print(f"   ✓ Config: maps_mode={config.get('maps_mode')}, reviews_source={config.get('reviews_source')}")
                
                # Verify config structure
                if not all(k in config for k in ['maps_mode', 'reviews_source', 'rating', 'intro']):
                    self.log_fail("GET /api/stores config structure", f"Missing required config fields. Got: {config}")
                
                # Verify rating structure
                if 'rating' in config:
                    rating = config['rating']
                    if not all(k in rating for k in ['avg', 'count']):
                        self.log_fail("GET /api/stores rating structure", f"Missing rating fields. Got: {rating}")
                
                # Verify we have 3 seeded locations
                if len(locations) != 3:
                    self.log_fail("GET /api/stores locations count", f"Expected 3 locations, got {len(locations)}")
                else:
                    print(f"   ✓ Verified 3 seeded locations")
            else:
                self.log_fail("GET /api/stores structure", f"Missing locations or config. Got: {response}")
        
        # Test 2: GET /api/store-reviews (public, should return reviews)
        print("\n--- Test 2: GET /api/store-reviews (public) ---")
        success, response = self.run_test(
            "GET /api/store-reviews returns reviews",
            "GET",
            "/store-reviews",
            200
        )
        if success and response:
            if 'source' in response and 'summary' in response and 'reviews' in response:
                source = response['source']
                summary = response['summary']
                reviews = response['reviews']
                print(f"   ✓ Source: {source}")
                print(f"   ✓ Summary: avg={summary.get('avg')}, count={summary.get('count')}")
                print(f"   ✓ Found {len(reviews)} reviews")
                
                # Verify summary structure
                if not all(k in summary for k in ['avg', 'count']):
                    self.log_fail("GET /api/store-reviews summary structure", f"Missing summary fields. Got: {summary}")
                
                # Verify we have 6 seeded reviews
                if len(reviews) != 6:
                    self.log_fail("GET /api/store-reviews count", f"Expected 6 reviews, got {len(reviews)}")
                else:
                    print(f"   ✓ Verified 6 seeded reviews")
            else:
                self.log_fail("GET /api/store-reviews structure", f"Missing required fields. Got: {response}")
        
        # Test 3: GET /api/admin/store-locations without auth (should return 401)
        print("\n--- Test 3: RBAC - GET /api/admin/store-locations without auth ---")
        success, response = self.run_test(
            "GET /api/admin/store-locations without auth returns 401",
            "GET",
            "/admin/store-locations",
            401
        )
        
        # Login as admin for remaining tests
        print("\n--- Logging in as admin ---")
        admin_success, admin_response = self.run_test(
            "Login as admin",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )
        
        if not admin_success or not admin_response or 'token' not in admin_response:
            print("❌ Cannot proceed with admin tests - login failed")
            return
        
        admin_token = admin_response['token']
        admin_headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
        
        # Test 4: GET /api/admin/store-locations (with auth)
        print("\n--- Test 4: GET /api/admin/store-locations (with auth) ---")
        success, response = self.run_test(
            "GET /api/admin/store-locations returns all locations",
            "GET",
            "/admin/store-locations",
            200,
            headers=admin_headers
        )
        if success and response:
            if isinstance(response, list):
                print(f"   ✓ Found {len(response)} locations")
            else:
                self.log_fail("GET /api/admin/store-locations type", f"Expected list, got: {type(response)}")
        
        # Test 5: POST /api/admin/store-locations (create new location)
        print("\n--- Test 5: POST /api/admin/store-locations (create) ---")
        new_location_data = {
            "name": f"Test Location {datetime.now().strftime('%H%M%S')}",
            "address": "Jl. Test No. 123, Bandung",
            "phone": "+62 857-1234-5678",
            "whatsapp": "6285712345678",
            "hours": "Setiap hari 09.00 – 20.00",
            "maps_query": "Jl. Test No. 123, Bandung",
            "map_url": "https://maps.app.goo.gl/test",
            "place_id": "",
            "order": 99,
            "active": True
        }
        success, response = self.run_test(
            "POST /api/admin/store-locations creates new location",
            "POST",
            "/admin/store-locations",
            200,
            data=new_location_data,
            headers=admin_headers
        )
        
        created_location_id = None
        if success and response:
            if 'id' in response and 'name' in response:
                created_location_id = response['id']
                print(f"   ✓ Created location with ID: {created_location_id}")
            else:
                self.log_fail("POST /api/admin/store-locations response", f"Missing id or name. Got: {response}")
        
        # Test 6: PUT /api/admin/store-locations/{id} (update location)
        if created_location_id:
            print("\n--- Test 6: PUT /api/admin/store-locations/{id} (update) ---")
            update_data = {
                "name": f"Updated Test Location {datetime.now().strftime('%H%M%S')}",
                "address": "Jl. Updated Test No. 456, Bandung",
                "phone": "+62 857-9999-9999",
                "active": True
            }
            success, response = self.run_test(
                "PUT /api/admin/store-locations/{id} updates location",
                "PUT",
                f"/admin/store-locations/{created_location_id}",
                200,
                data=update_data,
                headers=admin_headers
            )
            if success and response:
                if response.get('name') == update_data['name']:
                    print(f"   ✓ Location updated successfully")
                else:
                    self.log_fail("PUT /api/admin/store-locations update", f"Name not updated. Got: {response}")
        
        # Test 7: POST /api/admin/store-locations with missing required fields (should return 400)
        print("\n--- Test 7: POST /api/admin/store-locations with missing fields (validation) ---")
        invalid_data = {"name": "", "address": ""}
        success, response = self.run_test(
            "POST /api/admin/store-locations with empty name/address returns 400",
            "POST",
            "/admin/store-locations",
            400,
            data=invalid_data,
            headers=admin_headers
        )
        
        # Test 8: GET /api/admin/store-reviews (with auth)
        print("\n--- Test 8: GET /api/admin/store-reviews (with auth) ---")
        success, response = self.run_test(
            "GET /api/admin/store-reviews returns all reviews",
            "GET",
            "/admin/store-reviews",
            200,
            headers=admin_headers
        )
        if success and response:
            if isinstance(response, list):
                print(f"   ✓ Found {len(response)} reviews")
            else:
                self.log_fail("GET /api/admin/store-reviews type", f"Expected list, got: {type(response)}")
        
        # Test 9: POST /api/admin/store-reviews (create new review)
        print("\n--- Test 9: POST /api/admin/store-reviews (create) ---")
        new_review_data = {
            "author": f"Test Reviewer {datetime.now().strftime('%H%M%S')}",
            "rating": 5,
            "text": "Pelayanan sangat baik dan produk berkualitas!",
            "location": "Pasir Kaliki",
            "relative_time": "1 minggu lalu",
            "active": True
        }
        success, response = self.run_test(
            "POST /api/admin/store-reviews creates new review",
            "POST",
            "/admin/store-reviews",
            200,
            data=new_review_data,
            headers=admin_headers
        )
        
        created_review_id = None
        if success and response:
            if 'id' in response and 'author' in response:
                created_review_id = response['id']
                print(f"   ✓ Created review with ID: {created_review_id}")
            else:
                self.log_fail("POST /api/admin/store-reviews response", f"Missing id or author. Got: {response}")
        
        # Test 10: PUT /api/admin/store-reviews/{id} (update review)
        if created_review_id:
            print("\n--- Test 10: PUT /api/admin/store-reviews/{id} (update) ---")
            update_review_data = {
                "author": f"Updated Reviewer {datetime.now().strftime('%H%M%S')}",
                "rating": 4,
                "text": "Updated review text",
                "active": True
            }
            success, response = self.run_test(
                "PUT /api/admin/store-reviews/{id} updates review",
                "PUT",
                f"/admin/store-reviews/{created_review_id}",
                200,
                data=update_review_data,
                headers=admin_headers
            )
            if success and response:
                if response.get('author') == update_review_data['author']:
                    print(f"   ✓ Review updated successfully")
                else:
                    self.log_fail("PUT /api/admin/store-reviews update", f"Author not updated. Got: {response}")
        
        # Test 11: GET /api/admin/store-config
        print("\n--- Test 11: GET /api/admin/store-config ---")
        success, response = self.run_test(
            "GET /api/admin/store-config returns config",
            "GET",
            "/admin/store-config",
            200,
            headers=admin_headers
        )
        
        original_config = None
        if success and response:
            original_config = response
            expected_keys = ['maps_mode', 'reviews_source', 'google_maps_api_key', 'google_places_api_key', 
                           'google_place_id', 'store_rating_avg', 'store_rating_count', 'stores_intro']
            if all(k in response for k in expected_keys):
                print(f"   ✓ Config has all expected keys")
            else:
                self.log_fail("GET /api/admin/store-config keys", f"Missing keys. Got: {list(response.keys())}")
        
        # Test 12: PUT /api/admin/store-config (update config)
        print("\n--- Test 12: PUT /api/admin/store-config (update) ---")
        update_config_data = {
            "maps_mode": "js",
            "reviews_source": "google",
            "google_maps_api_key": "test_maps_key",
            "google_places_api_key": "test_places_key",
            "google_place_id": "ChIJtest123",
            "rating_avg": 4.8,
            "rating_count": 5000,
            "intro": "Test intro text"
        }
        success, response = self.run_test(
            "PUT /api/admin/store-config updates config",
            "PUT",
            "/admin/store-config",
            200,
            data=update_config_data,
            headers=admin_headers
        )
        if success and response:
            if response.get('maps_mode') == 'js' and response.get('reviews_source') == 'google':
                print(f"   ✓ Config updated successfully")
            else:
                self.log_fail("PUT /api/admin/store-config update", f"Config not updated. Got: {response}")
        
        # Test 13: Verify public config exposes maps_api_key only when mode=js
        print("\n--- Test 13: Verify public config exposes maps_api_key when mode=js ---")
        success, response = self.run_test(
            "GET /api/stores config exposes maps_api_key when mode=js",
            "GET",
            "/stores",
            200
        )
        if success and response:
            config = response.get('config', {})
            if config.get('maps_mode') == 'js' and 'maps_api_key' in config:
                print(f"   ✓ maps_api_key exposed when mode=js")
            else:
                self.log_fail("Public config maps_api_key", f"Expected maps_api_key when mode=js. Got: {config}")
        
        # Test 14: Revert config back to embed/manual (IMPORTANT for storefront)
        print("\n--- Test 14: Revert config to embed/manual ---")
        if original_config:
            revert_data = {
                "maps_mode": "embed",
                "reviews_source": "manual",
                "rating_avg": original_config.get('store_rating_avg', 4.5),
                "rating_count": original_config.get('store_rating_count', 3751),
                "intro": original_config.get('stores_intro', '')
            }
            success, response = self.run_test(
                "PUT /api/admin/store-config reverts to embed/manual",
                "PUT",
                "/admin/store-config",
                200,
                data=revert_data,
                headers=admin_headers
            )
            if success and response:
                if response.get('maps_mode') == 'embed' and response.get('reviews_source') == 'manual':
                    print(f"   ✓ Config reverted to embed/manual")
                else:
                    self.log_fail("Revert config", f"Config not reverted. Got: {response}")
        
        # Test 15: DELETE /api/admin/store-reviews/{id} (cleanup)
        if created_review_id:
            print("\n--- Test 15: DELETE /api/admin/store-reviews/{id} (cleanup) ---")
            success, response = self.run_test(
                "DELETE /api/admin/store-reviews/{id} deletes review",
                "DELETE",
                f"/admin/store-reviews/{created_review_id}",
                200,
                headers=admin_headers
            )
            if success and response:
                if response.get('deleted') is True:
                    print(f"   ✓ Review deleted successfully")
                else:
                    self.log_fail("DELETE review", f"Expected deleted:true. Got: {response}")
        
        # Test 16: DELETE /api/admin/store-locations/{id} (cleanup)
        if created_location_id:
            print("\n--- Test 16: DELETE /api/admin/store-locations/{id} (cleanup) ---")
            success, response = self.run_test(
                "DELETE /api/admin/store-locations/{id} deletes location",
                "DELETE",
                f"/admin/store-locations/{created_location_id}",
                200,
                headers=admin_headers
            )
            if success and response:
                if response.get('deleted') is True:
                    print(f"   ✓ Location deleted successfully")
                else:
                    self.log_fail("DELETE location", f"Expected deleted:true. Got: {response}")


    def test_facets_occasions_characters(self):
        """Test Occasions & Characters facet endpoints (public + admin CRUD)"""
        print("\n" + "="*60)
        print("TESTING OCCASIONS & CHARACTERS FACETS")
        print("="*60)
        
        # Test 1: GET /api/occasions - should return 8 active occasions sorted by order
        print("\n--- Test 1: GET /api/occasions ---")
        success, response = self.run_test(
            "GET /api/occasions returns 8 active occasions",
            "GET",
            "/occasions",
            200
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Occasions type", f"Expected array, got {type(response)}")
            elif len(response) != 8:
                self.log_fail("Occasions count", f"Expected 8 active occasions, got {len(response)}")
            else:
                print(f"   ✓ Returned {len(response)} occasions")
                # Check structure and sorting
                if len(response) > 0:
                    occ = response[0]
                    required_fields = ['id', 'slug', 'name', 'icon', 'order', 'active']
                    missing = [f for f in required_fields if f not in occ]
                    if missing:
                        self.log_fail("Occasion structure", f"Missing fields: {missing}")
                    else:
                        print(f"   ✓ Sample occasion: {occ.get('name')} (slug: {occ.get('slug')}, order: {occ.get('order')})")
                        # Check id prefix
                        if not occ.get('id', '').startswith('occ_'):
                            self.log_fail("Occasion ID prefix", f"Expected 'occ_' prefix, got: {occ.get('id')}")
                        # Check all are active
                        if not occ.get('active'):
                            self.log_fail("Occasion active", f"Expected active=true, got: {occ.get('active')}")
                
                # Verify sorting by order
                if len(response) >= 2:
                    orders = [o.get('order', 0) for o in response]
                    if orders != sorted(orders):
                        self.log_fail("Occasions sorting", f"Not sorted by order. Got: {orders}")
                    else:
                        print(f"   ✓ Occasions sorted by order: {orders}")
        
        # Test 2: GET /api/characters - should return 12 active characters sorted by order
        print("\n--- Test 2: GET /api/characters ---")
        success, response = self.run_test(
            "GET /api/characters returns 12 active characters",
            "GET",
            "/characters",
            200
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Characters type", f"Expected array, got {type(response)}")
            elif len(response) != 12:
                self.log_fail("Characters count", f"Expected 12 active characters, got {len(response)}")
            else:
                print(f"   ✓ Returned {len(response)} characters")
                # Check structure and sorting
                if len(response) > 0:
                    char = response[0]
                    required_fields = ['id', 'slug', 'name', 'icon', 'order', 'active']
                    missing = [f for f in required_fields if f not in char]
                    if missing:
                        self.log_fail("Character structure", f"Missing fields: {missing}")
                    else:
                        print(f"   ✓ Sample character: {char.get('name')} (slug: {char.get('slug')}, order: {char.get('order')})")
                        # Check id prefix
                        if not char.get('id', '').startswith('chr_'):
                            self.log_fail("Character ID prefix", f"Expected 'chr_' prefix, got: {char.get('id')}")
                
                # Verify sorting by order
                if len(response) >= 2:
                    orders = [c.get('order', 0) for c in response]
                    if orders != sorted(orders):
                        self.log_fail("Characters sorting", f"Not sorted by order. Got: {orders}")
                    else:
                        print(f"   ✓ Characters sorted by order: {orders}")
        
        # Test 3: GET /api/products?occasion=office - should filter correctly (~6 products)
        print("\n--- Test 3: GET /api/products?occasion=office ---")
        success, response = self.run_test(
            "GET /api/products?occasion=office filters correctly",
            "GET",
            "/products?occasion=office",
            200
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Products by occasion type", f"Expected array, got {type(response)}")
            else:
                print(f"   ✓ Filtered by occasion=office: {len(response)} products")
                # Check that products have 'office' in occasions array
                if len(response) > 0:
                    sample = response[0]
                    if 'occasions' not in sample:
                        self.log_fail("Product occasions field", f"Product missing 'occasions' field: {sample.get('id')}")
                    elif 'office' not in sample.get('occasions', []):
                        self.log_fail("Product occasion filter", f"Product {sample.get('id')} doesn't have 'office' in occasions: {sample.get('occasions')}")
                    else:
                        print(f"   ✓ Sample product {sample.get('name')} has occasions: {sample.get('occasions')}")
                
                # Expected ~6 products
                if len(response) < 4 or len(response) > 8:
                    print(f"   ⚠️  WARNING: Expected ~6 products with occasion=office, got {len(response)}")
        
        # Test 4: GET /api/products?character=fresh - should filter correctly (~4 products)
        print("\n--- Test 4: GET /api/products?character=fresh ---")
        success, response = self.run_test(
            "GET /api/products?character=fresh filters correctly",
            "GET",
            "/products?character=fresh",
            200
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Products by character type", f"Expected array, got {type(response)}")
            else:
                print(f"   ✓ Filtered by character=fresh: {len(response)} products")
                # Check that products have 'fresh' in characters array
                if len(response) > 0:
                    sample = response[0]
                    if 'characters' not in sample:
                        self.log_fail("Product characters field", f"Product missing 'characters' field: {sample.get('id')}")
                    elif 'fresh' not in sample.get('characters', []):
                        self.log_fail("Product character filter", f"Product {sample.get('id')} doesn't have 'fresh' in characters: {sample.get('characters')}")
                    else:
                        print(f"   ✓ Sample product {sample.get('name')} has characters: {sample.get('characters')}")
                
                # Expected ~4 products
                if len(response) < 2 or len(response) > 6:
                    print(f"   ⚠️  WARNING: Expected ~4 products with character=fresh, got {len(response)}")
        
        # Test 5: Multi-value filtering - ?occasion=office,gym
        print("\n--- Test 5: GET /api/products?occasion=office,gym (multi-value) ---")
        success, response = self.run_test(
            "GET /api/products?occasion=office,gym filters with multiple values",
            "GET",
            "/products?occasion=office,gym",
            200
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Products multi-occasion type", f"Expected array, got {type(response)}")
            else:
                print(f"   ✓ Filtered by occasion=office,gym: {len(response)} products")
                # Check that products have either 'office' or 'gym' in occasions
                if len(response) > 0:
                    sample = response[0]
                    occasions = sample.get('occasions', [])
                    if 'office' not in occasions and 'gym' not in occasions:
                        self.log_fail("Product multi-occasion filter", f"Product {sample.get('id')} has neither 'office' nor 'gym': {occasions}")
                    else:
                        print(f"   ✓ Sample product {sample.get('name')} has occasions: {occasions}")
        
        # Test 6: Admin CRUD - Login as admin first
        print("\n--- Test 6: Admin CRUD - Login ---")
        success, response = self.run_test(
            "Login as admin for facet CRUD",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )
        
        if not success or not response or 'token' not in response:
            print("   ❌ Cannot proceed with admin CRUD tests - login failed")
            return
        
        admin_token = response['token']
        admin_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {admin_token}'
        }
        print(f"   ✓ Admin logged in, token: {admin_token[:20]}...")
        
        # Test 7: GET /api/admin/occasions (all occasions, not just active)
        print("\n--- Test 7: GET /api/admin/occasions ---")
        success, response = self.run_test(
            "GET /api/admin/occasions returns all occasions",
            "GET",
            "/admin/occasions",
            200,
            headers=admin_headers
        )
        if success and response:
            print(f"   ✓ Admin occasions list: {len(response)} total")
        
        # Test 8: POST /api/admin/occasions - create new occasion
        print("\n--- Test 8: POST /api/admin/occasions (create) ---")
        new_occasion_data = {
            "name": "Test Occasion",
            "slug": "test-occasion",
            "icon": "TestIcon",
            "desc": "Test occasion for automated testing",
            "order": 999,
            "active": True
        }
        success, response = self.run_test(
            "POST /api/admin/occasions creates new occasion",
            "POST",
            "/admin/occasions",
            200,
            data=new_occasion_data,
            headers=admin_headers
        )
        
        created_occasion_id = None
        created_occasion_slug = None
        if success and response:
            created_occasion_id = response.get('id')
            created_occasion_slug = response.get('slug')
            print(f"   ✓ Created occasion: id={created_occasion_id}, slug={created_occasion_slug}")
            
            # Verify response structure
            if not created_occasion_id or not created_occasion_id.startswith('occ_'):
                self.log_fail("Create occasion ID", f"Expected 'occ_' prefix, got: {created_occasion_id}")
            if response.get('name') != new_occasion_data['name']:
                self.log_fail("Create occasion name", f"Expected '{new_occasion_data['name']}', got: {response.get('name')}")
        
        # Test 9: PUT /api/admin/occasions/{id} - update occasion
        if created_occasion_id:
            print("\n--- Test 9: PUT /api/admin/occasions/{id} (update) ---")
            update_data = {
                "name": "Updated Test Occasion",
                "icon": "UpdatedIcon",
                "order": 1000,
                "active": False
            }
            success, response = self.run_test(
                f"PUT /api/admin/occasions/{created_occasion_id} updates occasion",
                "PUT",
                f"/admin/occasions/{created_occasion_id}",
                200,
                data=update_data,
                headers=admin_headers
            )
            if success and response:
                if response.get('name') != update_data['name']:
                    self.log_fail("Update occasion name", f"Expected '{update_data['name']}', got: {response.get('name')}")
                if response.get('order') != update_data['order']:
                    self.log_fail("Update occasion order", f"Expected {update_data['order']}, got: {response.get('order')}")
                if response.get('active') != update_data['active']:
                    self.log_fail("Update occasion active", f"Expected {update_data['active']}, got: {response.get('active')}")
                print(f"   ✓ Updated occasion: name={response.get('name')}, order={response.get('order')}, active={response.get('active')}")
        
        # Test 10: DELETE /api/admin/occasions/{id} - delete unused occasion (should succeed)
        if created_occasion_id:
            print("\n--- Test 10: DELETE /api/admin/occasions/{id} (unused) ---")
            success, response = self.run_test(
                f"DELETE /api/admin/occasions/{created_occasion_id} deletes unused occasion",
                "DELETE",
                f"/admin/occasions/{created_occasion_id}",
                200,
                headers=admin_headers
            )
            if success and response:
                if response.get('deleted') is not True:
                    self.log_fail("Delete occasion", f"Expected deleted=true, got: {response}")
                else:
                    print(f"   ✓ Deleted unused occasion: {created_occasion_id}")
        
        # Test 11: DELETE /api/admin/occasions/{id} - try to delete IN-USE occasion (should fail with 400)
        print("\n--- Test 11: DELETE /api/admin/occasions/{id} (in-use, should fail) ---")
        # 'office' is used by products, so deleting it should fail
        # First, get the ID of 'office' occasion
        success, response = self.run_test(
            "GET /api/admin/occasions to find 'office' ID",
            "GET",
            "/admin/occasions",
            200,
            headers=admin_headers
        )
        
        office_occasion_id = None
        if success and response:
            for occ in response:
                if occ.get('slug') == 'office':
                    office_occasion_id = occ.get('id')
                    break
        
        if office_occasion_id:
            success, response = self.run_test(
                f"DELETE /api/admin/occasions/{office_occasion_id} (in-use) returns 400",
                "DELETE",
                f"/admin/occasions/{office_occasion_id}",
                400,
                headers=admin_headers
            )
            if success and response:
                print(f"   ✓ Delete blocked for in-use occasion: {response}")
        else:
            print("   ⚠️  WARNING: Could not find 'office' occasion to test delete blocking")
        
        # Test 12: POST /api/admin/characters - create new character
        print("\n--- Test 12: POST /api/admin/characters (create) ---")
        new_character_data = {
            "name": "Test Character",
            "slug": "test-character",
            "icon": "TestCharIcon",
            "desc": "Test character for automated testing",
            "order": 999,
            "active": True
        }
        success, response = self.run_test(
            "POST /api/admin/characters creates new character",
            "POST",
            "/admin/characters",
            200,
            data=new_character_data,
            headers=admin_headers
        )
        
        created_character_id = None
        if success and response:
            created_character_id = response.get('id')
            print(f"   ✓ Created character: id={created_character_id}, slug={response.get('slug')}")
            
            # Verify response structure
            if not created_character_id or not created_character_id.startswith('chr_'):
                self.log_fail("Create character ID", f"Expected 'chr_' prefix, got: {created_character_id}")
        
        # Test 13: DELETE /api/admin/characters/{id} - delete unused character
        if created_character_id:
            print("\n--- Test 13: DELETE /api/admin/characters/{id} (cleanup) ---")
            success, response = self.run_test(
                f"DELETE /api/admin/characters/{created_character_id} deletes unused character",
                "DELETE",
                f"/admin/characters/{created_character_id}",
                200,
                headers=admin_headers
            )
            if success and response:
                print(f"   ✓ Deleted unused character: {created_character_id}")
        
        # Test 14: Admin product save with facets - PUT /api/admin/products/{id}
        print("\n--- Test 14: PUT /api/admin/products/{id} with facets ---")
        # Use prd_greenbasillime as suggested
        product_id = "prd_greenbasillime"
        
        # First, get the current product data
        success, response = self.run_test(
            f"GET /api/admin/products/{product_id} to get current data",
            "GET",
            f"/admin/products/{product_id}",
            200,
            headers=admin_headers
        )
        
        if success and response:
            current_occasions = response.get('occasions', [])
            current_characters = response.get('characters', [])
            print(f"   ✓ Current facets: occasions={current_occasions}, characters={current_characters}")
            
            # Update with new facets - need to send complete product data
            update_data = {
                "name": response.get('name'),
                "brand": response.get('brand', 'Collector'),
                "category": response.get('category'),
                "concentration": response.get('concentration', 'EDP'),
                "gender": response.get('gender', 'Unisex'),
                "volumes": response.get('volumes', []),
                "notes": response.get('notes', {}),
                "description": response.get('description', ''),
                "performance": response.get('performance', {}),
                "images": response.get('images', []),
                "seo": response.get('seo', {}),
                "status": response.get('status', 'active'),
                "best_seller": response.get('best_seller', False),
                "is_new": response.get('is_new', False),
                "tags": response.get('tags', []),
                "occasions": ["office", "gym"],
                "characters": ["fresh", "elegant"]
            }
            
            success, update_response = self.run_test(
                f"PUT /api/admin/products/{product_id} with facets",
                "PUT",
                f"/admin/products/{product_id}",
                200,
                data=update_data,
                headers=admin_headers
            )
            
            if success and update_response:
                updated_occasions = update_response.get('occasions', [])
                updated_characters = update_response.get('characters', [])
                print(f"   ✓ Updated facets: occasions={updated_occasions}, characters={updated_characters}")
                
                # Verify the update
                if set(updated_occasions) != set(update_data['occasions']):
                    self.log_fail("Product occasions update", f"Expected {update_data['occasions']}, got {updated_occasions}")
                if set(updated_characters) != set(update_data['characters']):
                    self.log_fail("Product characters update", f"Expected {update_data['characters']}, got {updated_characters}")
                
                # Verify persistence by fetching again
                success, verify_response = self.run_test(
                    f"GET /api/admin/products/{product_id} to verify persistence",
                    "GET",
                    f"/admin/products/{product_id}",
                    200,
                    headers=admin_headers
                )
                
                if success and verify_response:
                    verified_occasions = verify_response.get('occasions', [])
                    verified_characters = verify_response.get('characters', [])
                    print(f"   ✓ Verified persistence: occasions={verified_occasions}, characters={verified_characters}")
                    
                    if set(verified_occasions) != set(update_data['occasions']):
                        self.log_fail("Product occasions persistence", f"Expected {update_data['occasions']}, got {verified_occasions}")
                    if set(verified_characters) != set(update_data['characters']):
                        self.log_fail("Product characters persistence", f"Expected {update_data['characters']}, got {verified_characters}")


    def test_backup_restore(self):
        """Test Backup & Restore APIs (admin-only)"""
        print("\n" + "="*60)
        print("TESTING BACKUP & RESTORE (NEW FEATURE)")
        print("="*60)
        
        # Setup: Login as admin and customer
        print("\n--- Setup: Login as admin and customer ---")
        admin_success, admin_response = self.run_test(
            "Login as admin",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )
        if not admin_success or not admin_response or 'token' not in admin_response:
            print("❌ Cannot proceed with backup tests - admin login failed")
            return
        
        admin_token = admin_response['token']
        admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        customer_success, customer_response = self.run_test(
            "Login as customer",
            "POST",
            "/auth/login",
            200,
            data={"email": "customer@collectorparfum.id", "password": "Customer#2026"}
        )
        if not customer_success or not customer_response or 'token' not in customer_response:
            print("❌ Cannot proceed with backup tests - customer login failed")
            return
        
        customer_token = customer_response['token']
        customer_headers = {"Authorization": f"Bearer {customer_token}", "Content-Type": "application/json"}
        
        # Test 1: RBAC - 401 without token
        print("\n--- Test 1: RBAC - 401 without token ---")
        success, response = self.run_test(
            "GET /api/admin/backup/collections without token returns 401",
            "GET",
            "/admin/backup/collections",
            401
        )
        
        # Test 2: RBAC - 403 with customer token
        print("\n--- Test 2: RBAC - 403 with customer token ---")
        success, response = self.run_test(
            "GET /api/admin/backup/collections with customer token returns 403",
            "GET",
            "/admin/backup/collections",
            403,
            headers=customer_headers
        )
        
        # Test 3: RBAC - 200 with admin token
        print("\n--- Test 3: RBAC - 200 with admin token ---")
        success, response = self.run_test(
            "GET /api/admin/backup/collections with admin token returns 200",
            "GET",
            "/admin/backup/collections",
            200,
            headers=admin_headers
        )
        
        # Test 4: List collections (exclude sessions)
        print("\n--- Test 4: List collections ---")
        success, response = self.run_test(
            "GET /api/admin/backup/collections returns list with name, label, count",
            "GET",
            "/admin/backup/collections",
            200,
            headers=admin_headers
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Collections list type", f"Expected list, got {type(response)}")
            else:
                print(f"   ✓ Returned {len(response)} collections")
                # Check structure
                if len(response) > 0:
                    c = response[0]
                    if not all(k in c for k in ["name", "label", "count"]):
                        self.log_fail("Collection structure", f"Missing required fields: {c}")
                # Check 'sessions' is excluded
                names = [c["name"] for c in response]
                if "sessions" in names:
                    self.log_fail("Sessions exclusion", "'sessions' should be excluded from collections list")
                else:
                    print("   ✓ 'sessions' excluded from list")
                if "backups" in names:
                    self.log_fail("Backups exclusion", "'backups' should be excluded from collections list")
                else:
                    print("   ✓ 'backups' excluded from list")
        
        # Test 5: Export backup (download JSON)
        print("\n--- Test 5: Export backup ---")
        try:
            url = f"{BASE_URL}/admin/backup/export"
            export_response = requests.post(
                url,
                json={"collections": ["categories"]},
                headers=admin_headers,
                timeout=120
            )
            self.tests_run += 1
            print("\n🔍 Testing: POST /api/admin/backup/export returns downloadable JSON")
            print(f"   Status: {export_response.status_code}")
            
            if export_response.status_code == 200:
                if export_response.headers.get("content-type") != "application/json":
                    self.log_fail("Export content-type", f"Expected application/json, got {export_response.headers.get('content-type')}")
                elif "attachment" not in export_response.headers.get("content-disposition", ""):
                    self.log_fail("Export disposition", "Expected attachment in content-disposition")
                else:
                    # Parse JSON
                    export_data = export_response.json()
                    if "meta" not in export_data or "data" not in export_data:
                        self.log_fail("Export structure", f"Missing meta or data: {export_data.keys()}")
                    elif "categories" not in export_data["data"]:
                        self.log_fail("Export data", "Missing 'categories' in data")
                    else:
                        self.log_pass("POST /api/admin/backup/export")
                        print(f"   ✓ Export backup: {len(export_data['data']['categories'])} categories")
                        # Save for upload restore test
                        import tempfile
                        import json
                        backup_file_path = f"{tempfile.gettempdir()}/test_backup_categories.json"
                        with open(backup_file_path, "w") as f:
                            json.dump(export_data, f)
                        print(f"   ✓ Saved backup to {backup_file_path}")
                        self.backup_file_path = backup_file_path
            else:
                self.log_fail("POST /api/admin/backup/export", f"Expected 200, got {export_response.status_code}")
        except Exception as e:
            self.log_fail("POST /api/admin/backup/export", f"Exception: {str(e)}")
        
        # Test 6: Create server backup
        print("\n--- Test 6: Create server backup ---")
        success, response = self.run_test(
            "POST /api/admin/backup/server creates backup",
            "POST",
            "/admin/backup/server",
            200,
            data={"collections": ["categories", "occasions"], "note": "Test backup"},
            headers=admin_headers
        )
        if success and response:
            required_fields = ["id", "filename", "collections", "counts", "size", "created_at"]
            missing = [f for f in required_fields if f not in response]
            if missing:
                self.log_fail("Server backup structure", f"Missing fields: {missing}")
            else:
                self.backup_id = response["id"]
                print(f"   ✓ Created server backup: {self.backup_id} ({response['size']} bytes)")
        
        # Test 7: List server backups
        print("\n--- Test 7: List server backups ---")
        success, response = self.run_test(
            "GET /api/admin/backup/server lists backups",
            "GET",
            "/admin/backup/server",
            200,
            headers=admin_headers
        )
        if success and response:
            if not isinstance(response, list):
                self.log_fail("Server backups list type", f"Expected list, got {type(response)}")
            else:
                print(f"   ✓ Listed {len(response)} server backups")
                if hasattr(self, 'backup_id'):
                    found = any(b["id"] == self.backup_id for b in response)
                    if not found:
                        self.log_fail("Server backup in list", f"Backup {self.backup_id} not found in list")
                    else:
                        print(f"   ✓ Found backup {self.backup_id} in list")
        
        # Test 8: Download server backup
        print("\n--- Test 8: Download server backup ---")
        if hasattr(self, 'backup_id'):
            try:
                url = f"{BASE_URL}/admin/backup/server/{self.backup_id}/download"
                download_response = requests.get(url, headers=admin_headers, timeout=120)
                self.tests_run += 1
                print(f"\n🔍 Testing: GET /api/admin/backup/server/{self.backup_id}/download")
                print(f"   Status: {download_response.status_code}")
                
                if download_response.status_code == 200:
                    if download_response.headers.get("content-type") != "application/json":
                        self.log_fail("Download content-type", f"Expected application/json, got {download_response.headers.get('content-type')}")
                    elif "attachment" not in download_response.headers.get("content-disposition", ""):
                        self.log_fail("Download disposition", "Expected attachment in content-disposition")
                    else:
                        download_data = download_response.json()
                        if "meta" not in download_data or "data" not in download_data:
                            self.log_fail("Download structure", f"Missing meta or data")
                        else:
                            self.log_pass(f"GET /api/admin/backup/server/{self.backup_id}/download")
                            print(f"   ✓ Downloaded server backup")
                else:
                    self.log_fail(f"GET /api/admin/backup/server/{self.backup_id}/download", f"Expected 200, got {download_response.status_code}")
            except Exception as e:
                self.log_fail(f"GET /api/admin/backup/server/{self.backup_id}/download", f"Exception: {str(e)}")
        
        # Test 9: Restore server backup (combine mode)
        print("\n--- Test 9: Restore server backup (combine mode) ---")
        if hasattr(self, 'backup_id'):
            success, response = self.run_test(
                "POST /api/admin/backup/server/{id}/restore with mode=combine",
                "POST",
                f"/admin/backup/server/{self.backup_id}/restore",
                200,
                data={"mode": "combine", "collections": ["categories"]},
                headers=admin_headers
            )
            if success and response:
                if response.get("mode") != "combine":
                    self.log_fail("Restore mode", f"Expected 'combine', got {response.get('mode')}")
                elif "restored" not in response or "summary" not in response:
                    self.log_fail("Restore structure", f"Missing restored or summary: {response.keys()}")
                else:
                    summary = response["summary"]
                    print(f"   ✓ Restore combine: {summary.get('collections')} collections, {summary.get('written')} docs written, {summary.get('errors')} errors")
        
        # Test 10: Restore server backup (overwrite mode on safe collection)
        print("\n--- Test 10: Restore server backup (overwrite mode) ---")
        if hasattr(self, 'backup_id'):
            success, response = self.run_test(
                "POST /api/admin/backup/server/{id}/restore with mode=overwrite",
                "POST",
                f"/admin/backup/server/{self.backup_id}/restore",
                200,
                data={"mode": "overwrite", "collections": ["categories"]},
                headers=admin_headers
            )
            if success and response:
                if response.get("mode") != "overwrite":
                    self.log_fail("Restore overwrite mode", f"Expected 'overwrite', got {response.get('mode')}")
                else:
                    for rep in response.get("restored", []):
                        if rep["collection"] == "categories":
                            print(f"   ✓ Overwrite categories: deleted={rep['deleted']}, inserted={rep['inserted']}")
                            break
        
        # Test 11: Restore from uploaded file
        print("\n--- Test 11: Restore from uploaded file ---")
        if hasattr(self, 'backup_file_path'):
            try:
                import os
                if os.path.exists(self.backup_file_path):
                    url = f"{BASE_URL}/admin/backup/restore"
                    with open(self.backup_file_path, "rb") as f:
                        files = {"file": ("test_backup.json", f, "application/json")}
                        data = {"mode": "combine", "collections": '["categories"]'}
                        upload_response = requests.post(url, files=files, data=data, headers={"Authorization": f"Bearer {admin_token}"}, timeout=180)
                    
                    self.tests_run += 1
                    print("\n🔍 Testing: POST /api/admin/backup/restore (multipart upload)")
                    print(f"   Status: {upload_response.status_code}")
                    
                    if upload_response.status_code == 200:
                        result = upload_response.json()
                        if result.get("mode") != "combine":
                            self.log_fail("Upload restore mode", f"Expected 'combine', got {result.get('mode')}")
                        elif "restored" not in result:
                            self.log_fail("Upload restore structure", f"Missing restored: {result.keys()}")
                        else:
                            self.log_pass("POST /api/admin/backup/restore (upload)")
                            print(f"   ✓ Restore upload: {result['summary']['collections']} collections, {result['summary']['written']} docs")
                    else:
                        self.log_fail("POST /api/admin/backup/restore (upload)", f"Expected 200, got {upload_response.status_code}")
                else:
                    print("   ⚠️  Skipping upload restore test: backup file not found")
            except Exception as e:
                self.log_fail("POST /api/admin/backup/restore (upload)", f"Exception: {str(e)}")
        
        # Test 12: Delete server backup
        print("\n--- Test 12: Delete server backup ---")
        if hasattr(self, 'backup_id'):
            success, response = self.run_test(
                "DELETE /api/admin/backup/server/{id} removes backup",
                "DELETE",
                f"/admin/backup/server/{self.backup_id}",
                200,
                headers=admin_headers
            )
            if success and response:
                if response.get("deleted") is not True:
                    self.log_fail("Delete backup", f"Expected deleted=True, got {response}")
                elif response.get("id") != self.backup_id:
                    self.log_fail("Delete backup ID", f"Expected {self.backup_id}, got {response.get('id')}")
                else:
                    print(f"   ✓ Deleted server backup {self.backup_id}")
                    # Verify it's gone
                    verify_success, verify_response = self.run_test(
                        "Verify backup removed from list",
                        "GET",
                        "/admin/backup/server",
                        200,
                        headers=admin_headers
                    )
                    if verify_success and verify_response:
                        found = any(b["id"] == self.backup_id for b in verify_response)
                        if found:
                            self.log_fail("Backup still in list", f"Backup {self.backup_id} still in list after delete")
                        else:
                            print("   ✓ Verified backup removed from list")


def main():
    print("="*60)
    print("COLLECTOR PARFUM - EPIC E1 + E2 + E3 + E4 + E7 BACKEND TESTS")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    
    tester = FoundationTester()
    
    # Run all test suites
    tester.test_health_endpoints()
    
    # Epic E1 - Catalog
    tester.test_products_list()
    tester.test_products_header()
    tester.test_products_filtering()
    tester.test_products_sorting()
    tester.test_products_pagination()
    tester.test_product_detail()
    tester.test_categories()
    tester.test_reviews()
    tester.test_adversarial()
    
    # Epic E2 - Vouchers
    tester.test_vouchers_validate()
    tester.test_vouchers_list()
    
    # Epic E3 - Cart, Checkout & Orders
    tester.test_config_endpoints()
    tester.test_cart_endpoints()
    tester.test_orders_guest_checkout()
    tester.test_orders_with_voucher()
    tester.test_orders_anti_oversell()
    tester.test_orders_invalid_inputs()
    tester.test_orders_list_auth()
    tester.test_orders_get_by_code()
    tester.test_orders_cancel()
    
    # Auth tests (needed for E3)
    tester.test_register_success()
    tester.test_register_duplicate()
    tester.test_register_validation()
    tester.test_login_success()
    tester.test_login_failures()
    tester.test_auth_me()
    
    # Epic E4 - Account tests
    tester.test_e4_account()
    
    # Epic E7 - Growth & Analytics tests
    tester.test_e7_analytics_event()
    tester.test_e7_sitemap()
    tester.test_e7_settings_growth_fields()
    tester.test_e7_admin_analytics()
    tester.test_e7_admin_crm()
    tester.test_e7_admin_settings_growth()
    
    # Epic E10 - Product Export/Import tests
    tester.test_e10_product_io()
    
    # Epic E11 - Store Locations & Google Reviews tests
    tester.test_store_locations_and_reviews()
    
    # Occasions & Characters Facets tests
    tester.test_facets_occasions_characters()
    
    # Backup & Restore tests (NEW FEATURE)
    tester.test_backup_restore()
    
    # Print summary and exit
    return tester.print_summary()


if __name__ == "__main__":
    sys.exit(main())
