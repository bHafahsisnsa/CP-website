"""Test P3: Server cart must persist variant_type field.

This test verifies that when a logged-in user saves their cart with variant_type,
the server correctly persists and returns the variant_type field.
"""
import os
import requests
import sys

BASE_URL = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/") + "/api"  # env-driven (jangan hardcode URL preview)

def test_p3_cart_variant_type():
    """Test that server cart persists variant_type field"""
    print("\n" + "="*60)
    print("TESTING P3: SERVER CART VARIANT_TYPE PERSISTENCE")
    print("="*60)
    
    # Step 1: Login as customer
    print("\n1. Login as customer@collectorparfum.id...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "customer@collectorparfum.id", "password": "Customer#2026"},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ FAIL: Login failed with status {login_response.status_code}")
        return False
    
    token = login_response.json().get("token")
    print(f"✅ Login successful, token: {token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: PUT cart with variant_type="Premium"
    print("\n2. PUT /api/cart with variant_type='Premium'...")
    cart_data = {
        "items": [
            {
                "product_id": "prd_noiroudintense",
                "variant_type": "Premium",
                "volume_ml": 50,
                "quantity": 1
            }
        ],
        "voucher_code": None,
        "note": ""
    }
    
    put_response = requests.put(
        f"{BASE_URL}/cart",
        json=cart_data,
        headers=headers,
        timeout=10
    )
    
    if put_response.status_code != 200:
        print(f"❌ FAIL: PUT cart failed with status {put_response.status_code}")
        print(f"Response: {put_response.text}")
        return False
    
    put_data = put_response.json()
    print(f"✅ PUT cart successful")
    print(f"   Response: {put_data}")
    
    # Step 3: GET cart and verify variant_type is returned
    print("\n3. GET /api/cart and verify variant_type...")
    get_response = requests.get(
        f"{BASE_URL}/cart",
        headers=headers,
        timeout=10
    )
    
    if get_response.status_code != 200:
        print(f"❌ FAIL: GET cart failed with status {get_response.status_code}")
        return False
    
    get_data = get_response.json()
    print(f"✅ GET cart successful")
    print(f"   Response: {get_data}")
    
    # Verify items exist
    items = get_data.get("items", [])
    if not items:
        print("❌ FAIL: No items in cart")
        return False
    
    # Verify first item has variant_type
    first_item = items[0]
    variant_type = first_item.get("variant_type")
    
    print(f"\n4. Verification:")
    print(f"   Item: {first_item}")
    print(f"   variant_type: '{variant_type}'")
    
    if variant_type != "Premium":
        print(f"❌ FAIL: Expected variant_type='Premium', got '{variant_type}'")
        return False
    
    print(f"✅ PASS: variant_type is correctly persisted as 'Premium'")
    
    # Additional test: PUT cart with empty variant_type (typeless product)
    print("\n5. Additional test: PUT cart with empty variant_type...")
    cart_data_typeless = {
        "items": [
            {
                "product_id": "prd_blancnerolibloom",
                "variant_type": "",
                "volume_ml": 30,
                "quantity": 1
            }
        ],
        "voucher_code": None,
        "note": ""
    }
    
    put_response2 = requests.put(
        f"{BASE_URL}/cart",
        json=cart_data_typeless,
        headers=headers,
        timeout=10
    )
    
    if put_response2.status_code != 200:
        print(f"❌ FAIL: PUT cart (typeless) failed with status {put_response2.status_code}")
        return False
    
    get_response2 = requests.get(
        f"{BASE_URL}/cart",
        headers=headers,
        timeout=10
    )
    
    if get_response2.status_code != 200:
        print(f"❌ FAIL: GET cart (typeless) failed")
        return False
    
    get_data2 = get_response2.json()
    items2 = get_data2.get("items", [])
    if items2:
        variant_type2 = items2[0].get("variant_type")
        print(f"   Typeless product variant_type: '{variant_type2}'")
        if variant_type2 == "":
            print(f"✅ PASS: Empty variant_type correctly persisted")
        else:
            print(f"⚠️  WARNING: Expected empty string, got '{variant_type2}'")
    
    return True

if __name__ == "__main__":
    try:
        success = test_p3_cart_variant_type()
        if success:
            print("\n" + "="*60)
            print("✅ P3 TEST PASSED: Server cart correctly persists variant_type")
            print("="*60)
            sys.exit(0)
        else:
            print("\n" + "="*60)
            print("❌ P3 TEST FAILED")
            print("="*60)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
