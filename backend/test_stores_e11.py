"""test_stores_e11.py — Epic E11 Store Locations + Google Reviews backend testing.

Tests:
- PUBLIC: GET /api/stores (locations + config)
- PUBLIC: GET /api/store-reviews (manual curated reviews)
- ADMIN: CRUD /api/admin/store-locations
- ADMIN: CRUD /api/admin/store-reviews
- ADMIN: GET/PUT /api/admin/store-config
- RBAC: 401 without token
- Validation: 422 for missing required fields
"""
import os
import requests
import sys

BASE_URL = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/") + "/api"  # env-driven (jangan hardcode URL preview)

class StoresE11Tester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.admin_token = None
        self.created_location_id = None
        self.created_review_id = None

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

    def test_admin_login(self):
        """Login as admin to get token"""
        print("\n" + "="*60)
        print("ADMIN LOGIN")
        print("="*60)
        
        success, response = self.run_test(
            "Admin login",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@collectorparfum.id", "password": "Admin#2026"}
        )
        
        if success and response and 'token' in response:
            self.admin_token = response['token']
            print(f"   ✓ Admin token obtained")
            return True
        else:
            print(f"   ✗ Failed to get admin token")
            return False

    def test_public_stores(self):
        """Test GET /api/stores"""
        print("\n" + "="*60)
        print("PUBLIC STORES API")
        print("="*60)
        
        success, response = self.run_test(
            "GET /api/stores returns locations and config",
            "GET",
            "/stores",
            200
        )
        
        if success and response:
            # Verify structure
            if 'locations' not in response:
                self.log_fail("GET /api/stores structure", "Missing 'locations' field")
                return False
            if 'config' not in response:
                self.log_fail("GET /api/stores structure", "Missing 'config' field")
                return False
            
            locations = response['locations']
            config = response['config']
            
            print(f"   ✓ Found {len(locations)} locations")
            print(f"   ✓ Config: maps_mode={config.get('maps_mode')}, reviews_source={config.get('reviews_source')}")
            
            # Verify expected data
            if len(locations) < 3:
                self.log_fail("GET /api/stores data", f"Expected at least 3 locations, got {len(locations)}")
            else:
                print(f"   ✓ At least 3 locations present")
            
            if config.get('maps_mode') != 'embed':
                self.log_fail("GET /api/stores config", f"Expected maps_mode='embed', got '{config.get('maps_mode')}'")
            else:
                print(f"   ✓ maps_mode is 'embed'")
            
            if config.get('reviews_source') != 'manual':
                self.log_fail("GET /api/stores config", f"Expected reviews_source='manual', got '{config.get('reviews_source')}'")
            else:
                print(f"   ✓ reviews_source is 'manual'")
            
            rating = config.get('rating', {})
            if rating.get('avg') != 4.5:
                self.log_fail("GET /api/stores rating", f"Expected rating avg=4.5, got {rating.get('avg')}")
            else:
                print(f"   ✓ Rating avg is 4.5")
            
            if rating.get('count') != 3751:
                self.log_fail("GET /api/stores rating", f"Expected rating count=3751, got {rating.get('count')}")
            else:
                print(f"   ✓ Rating count is 3751")
            
            return True
        
        return False

    def test_public_reviews(self):
        """Test GET /api/store-reviews"""
        print("\n" + "="*60)
        print("PUBLIC STORE REVIEWS API")
        print("="*60)
        
        success, response = self.run_test(
            "GET /api/store-reviews returns manual curated reviews",
            "GET",
            "/store-reviews",
            200
        )
        
        if success and response:
            # Verify structure
            if 'source' not in response:
                self.log_fail("GET /api/store-reviews structure", "Missing 'source' field")
                return False
            if 'summary' not in response:
                self.log_fail("GET /api/store-reviews structure", "Missing 'summary' field")
                return False
            if 'reviews' not in response:
                self.log_fail("GET /api/store-reviews structure", "Missing 'reviews' field")
                return False
            
            source = response['source']
            summary = response['summary']
            reviews = response['reviews']
            
            print(f"   ✓ Source: {source}")
            print(f"   ✓ Summary: avg={summary.get('avg')}, count={summary.get('count')}")
            print(f"   ✓ Found {len(reviews)} reviews")
            
            # Verify expected data
            if source != 'manual':
                self.log_fail("GET /api/store-reviews source", f"Expected source='manual', got '{source}'")
            else:
                print(f"   ✓ Source is 'manual'")
            
            if len(reviews) < 6:
                self.log_fail("GET /api/store-reviews data", f"Expected at least 6 reviews, got {len(reviews)}")
            else:
                print(f"   ✓ At least 6 reviews present")
            
            return True
        
        return False

    def test_admin_locations_crud(self):
        """Test admin CRUD for store locations"""
        print("\n" + "="*60)
        print("ADMIN STORE LOCATIONS CRUD")
        print("="*60)
        
        if not self.admin_token:
            print("   ✗ Skipping: No admin token")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # List locations
        success, response = self.run_test(
            "GET /api/admin/store-locations",
            "GET",
            "/admin/store-locations",
            200,
            headers=headers
        )
        
        if success and response:
            print(f"   ✓ Listed {len(response)} locations")
        
        # Create location
        new_location = {
            "name": "Test Location E11",
            "address": "Jl. Test No. 123, Bandung",
            "phone": "+62 857-1234-5678",
            "whatsapp": "6285712345678",
            "hours": "Setiap hari 09.00 – 21.00",
            "maps_query": "Jl. Test No. 123, Bandung",
            "map_url": "https://maps.app.goo.gl/test123",
            "active": True
        }
        
        success, response = self.run_test(
            "POST /api/admin/store-locations (create)",
            "POST",
            "/admin/store-locations",
            200,
            data=new_location,
            headers=headers
        )
        
        if success and response and 'id' in response:
            self.created_location_id = response['id']
            print(f"   ✓ Created location with ID: {self.created_location_id}")
        else:
            print(f"   ✗ Failed to create location")
            return False
        
        # Update location
        update_data = {
            "name": "Test Location E11 Updated",
            "address": "Jl. Test No. 456, Bandung",
            "phone": "+62 857-9999-9999",
            "whatsapp": "6285799999999",
            "hours": "Setiap hari 10.00 – 22.00",
            "maps_query": "Jl. Test No. 456, Bandung",
            "map_url": "https://maps.app.goo.gl/test456",
            "active": True
        }
        
        success, response = self.run_test(
            "PUT /api/admin/store-locations/{id} (update)",
            "PUT",
            f"/admin/store-locations/{self.created_location_id}",
            200,
            data=update_data,
            headers=headers
        )
        
        if success and response:
            if response.get('name') == "Test Location E11 Updated":
                print(f"   ✓ Location updated successfully")
            else:
                self.log_fail("Location update verification", f"Name not updated. Got: {response.get('name')}")
        
        # Delete location
        success, response = self.run_test(
            "DELETE /api/admin/store-locations/{id}",
            "DELETE",
            f"/admin/store-locations/{self.created_location_id}",
            200,
            headers=headers
        )
        
        if success:
            print(f"   ✓ Location deleted successfully")
        
        return True

    def test_admin_reviews_crud(self):
        """Test admin CRUD for store reviews"""
        print("\n" + "="*60)
        print("ADMIN STORE REVIEWS CRUD")
        print("="*60)
        
        if not self.admin_token:
            print("   ✗ Skipping: No admin token")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # List reviews
        success, response = self.run_test(
            "GET /api/admin/store-reviews",
            "GET",
            "/admin/store-reviews",
            200,
            headers=headers
        )
        
        if success and response:
            print(f"   ✓ Listed {len(response)} reviews")
        
        # Create review
        new_review = {
            "author": "Test Reviewer E11",
            "rating": 5,
            "text": "Pelayanan sangat baik dan produk berkualitas!",
            "location": "Pasir Kaliki",
            "relative_time": "1 minggu lalu",
            "active": True
        }
        
        success, response = self.run_test(
            "POST /api/admin/store-reviews (create)",
            "POST",
            "/admin/store-reviews",
            200,
            data=new_review,
            headers=headers
        )
        
        if success and response and 'id' in response:
            self.created_review_id = response['id']
            print(f"   ✓ Created review with ID: {self.created_review_id}")
        else:
            print(f"   ✗ Failed to create review")
            return False
        
        # Update review
        update_data = {
            "author": "Test Reviewer E11 Updated",
            "rating": 4,
            "text": "Pelayanan baik, produk berkualitas tinggi!",
            "location": "Cihampelas",
            "relative_time": "2 minggu lalu",
            "active": True
        }
        
        success, response = self.run_test(
            "PUT /api/admin/store-reviews/{id} (update)",
            "PUT",
            f"/admin/store-reviews/{self.created_review_id}",
            200,
            data=update_data,
            headers=headers
        )
        
        if success and response:
            if response.get('author') == "Test Reviewer E11 Updated":
                print(f"   ✓ Review updated successfully")
            else:
                self.log_fail("Review update verification", f"Author not updated. Got: {response.get('author')}")
        
        # Delete review
        success, response = self.run_test(
            "DELETE /api/admin/store-reviews/{id}",
            "DELETE",
            f"/admin/store-reviews/{self.created_review_id}",
            200,
            headers=headers
        )
        
        if success:
            print(f"   ✓ Review deleted successfully")
        
        return True

    def test_admin_config(self):
        """Test admin store config get/update"""
        print("\n" + "="*60)
        print("ADMIN STORE CONFIG")
        print("="*60)
        
        if not self.admin_token:
            print("   ✗ Skipping: No admin token")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # Get config
        success, response = self.run_test(
            "GET /api/admin/store-config",
            "GET",
            "/admin/store-config",
            200,
            headers=headers
        )
        
        if success and response:
            print(f"   ✓ Config retrieved")
            original_intro = response.get('stores_intro', '')
        else:
            return False
        
        # Update config
        update_data = {
            "rating_avg": 4.6,
            "rating_count": 4000,
            "intro": "Test intro updated by E11 test"
        }
        
        success, response = self.run_test(
            "PUT /api/admin/store-config (update)",
            "PUT",
            "/admin/store-config",
            200,
            data=update_data,
            headers=headers
        )
        
        if success and response:
            if response.get('store_rating_avg') == 4.6:
                print(f"   ✓ Config rating_avg updated to 4.6")
            else:
                self.log_fail("Config update verification", f"rating_avg not updated. Got: {response.get('store_rating_avg')}")
            
            if response.get('store_rating_count') == 4000:
                print(f"   ✓ Config rating_count updated to 4000")
            else:
                self.log_fail("Config update verification", f"rating_count not updated. Got: {response.get('store_rating_count')}")
        
        # Restore original config
        restore_data = {
            "rating_avg": 4.5,
            "rating_count": 3751,
            "intro": original_intro
        }
        
        success, response = self.run_test(
            "PUT /api/admin/store-config (restore)",
            "PUT",
            "/admin/store-config",
            200,
            data=restore_data,
            headers=headers
        )
        
        if success:
            print(f"   ✓ Config restored to original values")
        
        return True

    def test_rbac(self):
        """Test RBAC - 401 without token"""
        print("\n" + "="*60)
        print("RBAC TESTS")
        print("="*60)
        
        # Try to access admin endpoint without token
        success, response = self.run_test(
            "GET /api/admin/store-locations without token returns 401",
            "GET",
            "/admin/store-locations",
            401
        )
        
        return success

    def test_validation(self):
        """Test validation - 422 for missing required fields"""
        print("\n" + "="*60)
        print("VALIDATION TESTS")
        print("="*60)
        
        if not self.admin_token:
            print("   ✗ Skipping: No admin token")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # Try to create location without name
        invalid_location = {
            "address": "Jl. Test No. 123, Bandung"
        }
        
        success, response = self.run_test(
            "POST /api/admin/store-locations without name returns 422",
            "POST",
            "/admin/store-locations",
            422,
            data=invalid_location,
            headers=headers
        )
        
        return success

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        
        if self.failures:
            print("\n❌ FAILED TESTS:")
            for failure in self.failures:
                print(f"  - {failure['test']}: {failure['reason']}")
        
        if self.tests_failed == 0:
            print("\n✅ ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n❌ {self.tests_failed} TEST(S) FAILED")
            return 1

def main():
    tester = StoresE11Tester()
    
    # Run tests in order
    tester.test_admin_login()
    tester.test_public_stores()
    tester.test_public_reviews()
    tester.test_admin_locations_crud()
    tester.test_admin_reviews_crud()
    tester.test_admin_config()
    tester.test_rbac()
    tester.test_validation()
    
    return tester.print_summary()

if __name__ == "__main__":
    sys.exit(main())
