#!/usr/bin/env python3
"""Backend API test for iteration 41 - Content & Settings verification"""
import requests
import sys

BASE_URL = "https://multi-admin-io.preview.emergentagent.com"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name, condition, details=""):
        self.tests.append(name)
        if condition:
            self.passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            self.failed += 1
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
        return condition
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"BACKEND TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {total} | Passed: {self.passed} | Failed: {self.failed}")
        print(f"{'='*60}\n")
        return 0 if self.failed == 0 else 1

def main():
    t = TestRunner()
    
    print(f"\n{'='*60}")
    print(f"BACKEND API TEST - ITERATION 41")
    print(f"Testing: {BASE_URL}")
    print(f"{'='*60}\n")
    
    # ========== PRIORITY 3: API Tests ==========
    print("PRIORITY 3: API TESTS\n")
    
    # Test 1: GET /api/health
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=10)
        t.test("GET /api/health returns 200", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            t.test("Health check has 'status' field", "status" in data, f"Response: {data}")
    except Exception as e:
        t.test("GET /api/health returns 200", False, f"Error: {e}")
    
    # Test 2: GET /api/settings - verify new content
    try:
        r = requests.get(f"{BASE_URL}/api/settings", timeout=10)
        t.test("GET /api/settings returns 200", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            
            # Check support_email
            email = data.get("support_email", "")
            t.test("support_email is 'cs@collectorparfum.com'", 
                   email == "cs@collectorparfum.com", 
                   f"Found: {email}")
            
            # Check whatsapp_number
            wa = data.get("whatsapp_number", "")
            t.test("whatsapp_number is '6285720000105'", 
                   wa == "6285720000105", 
                   f"Found: {wa}")
            
            # Check NO old placeholders
            json_str = str(data)
            t.test("NO 'hello@collectorparfum.id' in settings", 
                   "hello@collectorparfum.id" not in json_str,
                   "Old placeholder check")
            t.test("NO '+62 812-3456-7890' in settings", 
                   "+62 812-3456-7890" not in json_str,
                   "Old placeholder check")
    except Exception as e:
        t.test("GET /api/settings returns 200", False, f"Error: {e}")
    
    # Test 3: GET /api/content - verify 20 sections and about.title contains '1970'
    try:
        r = requests.get(f"{BASE_URL}/api/content", timeout=10)
        t.test("GET /api/content returns 200", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            
            # Check number of sections
            section_count = len(data)
            t.test("Content has 20 sections", 
                   section_count == 20, 
                   f"Found: {section_count} sections")
            
            # Check about section contains '1970'
            about = data.get("about", {})
            about_title = about.get("title", "")
            t.test("about.title contains '1970'", 
                   "1970" in about_title, 
                   f"Title: {about_title}")
            
            # Check about intro mentions key history
            about_intro = about.get("intro", "")
            t.test("about.intro mentions '8 September 1970'", 
                   "8 September 1970" in about_intro,
                   f"Intro length: {len(about_intro)} chars")
            t.test("about.intro mentions 'Jalan Kolektor'", 
                   "Jalan Kolektor" in about_intro,
                   "History check")
            t.test("about.intro mentions 'Paledang'", 
                   "Paledang" in about_intro,
                   "History check")
            
            # Check contact section
            contact = data.get("contact", {})
            contact_items = contact.get("items", [])
            t.test("contact section has items", 
                   len(contact_items) >= 6,
                   f"Found: {len(contact_items)} contact items")
            
            # Check for cs@collectorparfum.com in contact
            contact_str = str(contact)
            t.test("contact contains 'cs@collectorparfum.com'", 
                   "cs@collectorparfum.com" in contact_str,
                   "Email check")
            t.test("contact contains '+62 857-2000-0105'", 
                   "+62 857-2000-0105" in contact_str or "6285720000105" in contact_str,
                   "WhatsApp check")
            
            # Check NO old placeholders in content
            content_str = str(data)
            t.test("NO 'hello@collectorparfum.id' in content", 
                   "hello@collectorparfum.id" not in content_str,
                   "Old placeholder check")
            t.test("NO 'Cempaka Putih' in content", 
                   "Cempaka Putih" not in content_str,
                   "Old placeholder check")
            t.test("NO 'Jakarta Pusat' in content", 
                   "Jakarta Pusat" not in content_str,
                   "Old placeholder check")
            
            # Check FAQ section
            faq = data.get("faq", {})
            faq_items = faq.get("items", [])
            if len(faq_items) > 0:
                faq_str = str(faq_items)
                t.test("FAQ mentions WhatsApp +62 857-2000-0105", 
                       "+62 857-2000-0105" in faq_str or "6285720000105" in faq_str,
                       "FAQ WhatsApp check")
                t.test("FAQ mentions LINE @collectorparfum", 
                       "@collectorparfum" in faq_str,
                       "FAQ LINE check")
            
            # Check announcement bar
            announcement = data.get("announcement", {})
            ann_items = announcement.get("items", [])
            if len(ann_items) > 0:
                ann_str = " ".join(ann_items)
                t.test("Announcement contains 'Refill Perfume Distributor Since 1970'", 
                       "Refill Perfume Distributor Since 1970" in ann_str,
                       f"Found {len(ann_items)} announcement items")
                t.test("Announcement contains '3 Cabang di Bandung'", 
                       "3 Cabang di Bandung" in ann_str or "Cabang" in ann_str,
                       "Branch info check")
    except Exception as e:
        t.test("GET /api/content returns 200", False, f"Error: {e}")
    
    # Test 4: GET /api/products - verify 12 products
    try:
        r = requests.get(f"{BASE_URL}/api/products", timeout=10)
        t.test("GET /api/products returns 200", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            products = data.get("products", [])
            t.test("Products list has 12 items", 
                   len(products) == 12,
                   f"Found: {len(products)} products")
    except Exception as e:
        t.test("GET /api/products returns 200", False, f"Error: {e}")
    
    # Test 5: GET /api/categories
    try:
        r = requests.get(f"{BASE_URL}/api/categories", timeout=10)
        t.test("GET /api/categories returns 200", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        t.test("GET /api/categories returns 200", False, f"Error: {e}")
    
    # Test 6: GET /api/stores - verify 3 locations
    try:
        r = requests.get(f"{BASE_URL}/api/stores", timeout=10)
        t.test("GET /api/stores returns 200", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            locations = data.get("locations", [])
            t.test("Store locations has 3 branches", 
                   len(locations) == 3,
                   f"Found: {len(locations)} locations")
            
            if len(locations) >= 3:
                loc_str = str(locations)
                t.test("Locations include 'Paledang'", 
                       "Paledang" in loc_str,
                       "Branch check")
                t.test("Locations include 'Pasir Kaliki' or 'Pasirkaliki'", 
                       "Pasir Kaliki" in loc_str or "Pasirkaliki" in loc_str,
                       "Branch check")
                t.test("Locations include 'Gatot Subroto'", 
                       "Gatot Subroto" in loc_str,
                       "Branch check")
                
                # Check hours format
                t.test("Locations have operating hours", 
                       any("09.00" in str(loc.get("hours", "")) for loc in locations),
                       "Hours check")
    except Exception as e:
        t.test("GET /api/stores returns 200", False, f"Error: {e}")
    
    return t.summary()

if __name__ == "__main__":
    sys.exit(main())
