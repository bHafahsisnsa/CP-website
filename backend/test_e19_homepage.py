"""
Test script for E19 - Collector Parfum homepage fixes
Tests:
1. GET /api/products?limit=100 returns 12 products
2. GET /api/categories returns 200
"""
import os
import requests
import sys

BASE_URL = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/") + "/api"  # env-driven (jangan hardcode URL preview)

def test_products_endpoint():
    """Test GET /api/products?limit=100 returns 12 products"""
    print("\n" + "="*60)
    print("TESTING GET /api/products?limit=100")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/products?limit=100"
        response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        products = response.json()
        
        if not isinstance(products, list):
            print(f"❌ FAIL: Expected array, got {type(products)}")
            return False
        
        print(f"✅ PASS: Returned {len(products)} products")
        
        if len(products) < 12:
            print(f"❌ FAIL: Expected at least 12 products, got {len(products)}")
            return False
        
        print(f"✅ PASS: Product count >= 12")
        
        # Check first product structure
        if len(products) > 0:
            p = products[0]
            required_fields = ['id', 'slug', 'name', 'category', 'price', 'volumes', 
                             'notes', 'rating_avg', 'rating_count', 'images', 'status']
            missing = [f for f in required_fields if f not in p]
            if missing:
                print(f"❌ FAIL: Product missing fields: {missing}")
                return False
            
            print(f"✅ PASS: Product structure valid")
            print(f"   Sample: {p.get('name')} (id: {p.get('id')})")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")
        return False

def test_categories_endpoint():
    """Test GET /api/categories returns 200"""
    print("\n" + "="*60)
    print("TESTING GET /api/categories")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/categories"
        response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        categories = response.json()
        
        if not isinstance(categories, list):
            print(f"❌ FAIL: Expected array, got {type(categories)}")
            return False
        
        print(f"✅ PASS: Returned {len(categories)} categories")
        
        # Check first category structure
        if len(categories) > 0:
            c = categories[0]
            required_fields = ['id', 'slug', 'name', 'active']
            missing = [f for f in required_fields if f not in c]
            if missing:
                print(f"❌ FAIL: Category missing fields: {missing}")
                return False
            
            print(f"✅ PASS: Category structure valid")
            print(f"   Sample: {c.get('name')} (id: {c.get('id')})")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("E19 HOMEPAGE BACKEND TESTS")
    print("="*60)
    
    results = []
    
    # Test products endpoint
    results.append(("Products endpoint", test_products_endpoint()))
    
    # Test categories endpoint
    results.append(("Categories endpoint", test_categories_endpoint()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
