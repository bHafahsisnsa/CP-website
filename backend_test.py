"""backend_test.py — Media Manager API Testing

Tests critical user stories for E20 Media Manager:
- Admin can upload images locally (not just URLs)
- Images are stored on disk and render correctly (not broken)
- Media picker integration with products
- Nested folders work
- Self-heal mechanism works
"""
import io
import os
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

BASE_URL = os.environ.get("BASE_URL", "https://media-manager-local.preview.emergentagent.com")
API = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@collectorparfum.id"
ADMIN_PASSWORD = "Admin#2026"
CUSTOMER_EMAIL = "customer@collectorparfum.id"
CUSTOMER_PASSWORD = "Customer#2026"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.total = 0
    
    def add_pass(self, name, detail=""):
        self.passed.append(name)
        self.total += 1
        print(f"✓ {name}" + (f" ({detail})" if detail else ""))
    
    def add_fail(self, name, detail=""):
        self.failed.append((name, detail))
        self.total += 1
        print(f"✗ {name} — {detail}")
    
    def check(self, condition, name, detail=""):
        if condition:
            self.add_pass(name, detail)
        else:
            self.add_fail(name, detail or "condition failed")
        return bool(condition)
    
    def summary(self):
        print(f"\n{'='*60}")
        print(f"RESULTS: {len(self.passed)} PASS / {len(self.failed)} FAIL (total {self.total})")
        if self.failed:
            print("\nFAILURES:")
            for name, detail in self.failed:
                print(f"  - {name}: {detail}")
        print(f"{'='*60}")
        return 0 if not self.failed else 1


def create_test_image(width=800, height=600, format="JPEG"):
    """Create a test image in memory"""
    img = Image.new("RGB", (width, height), color=(73, 109, 137))
    # Add some pattern so it's not just solid color
    pixels = img.load()
    for y in range(height):
        for x in range(0, width, 20):
            pixels[x, y] = (x % 255, y % 255, 100)
    
    buf = io.BytesIO()
    img.save(buf, format=format, quality=85)
    return buf.getvalue()


def main():
    results = TestResults()
    
    with httpx.Client(timeout=60.0) as client:
        print("\n=== BACKEND API TESTING: Media Manager ===\n")
        
        # ========== 1. AUTHENTICATION ==========
        print("\n--- 1. Authentication ---")
        r = client.post(f"{API}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        results.check(r.status_code == 200, "Admin login", f"status {r.status_code}")
        
        if r.status_code != 200:
            print(f"FATAL: Cannot login. Run: python scripts/seed_data.py")
            return 1
        
        token = r.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # ========== 2. MEDIA STATS & CONFIG ==========
        print("\n--- 2. Media Stats & Configuration ---")
        r = client.get(f"{API}/admin/media/stats", headers=headers)
        results.check(r.status_code == 200, "GET /admin/media/stats", f"status {r.status_code}")
        
        if r.status_code == 200:
            stats = r.json()
            results.check(stats.get("max_mb") >= 15, "Upload limit >= 15MB", f"{stats.get('max_mb')}MB")
            results.check(stats.get("mirror") is True, "MongoDB GridFS mirror enabled", "self-heal ready")
            print(f"   Stats: {stats.get('assets')} assets, {stats.get('folders')} folders, {stats.get('bytes')//1024}KB used")
        
        # ========== 3. FOLDER OPERATIONS ==========
        print("\n--- 3. Folder Operations (Nested) ---")
        ts = str(int(time.time()))
        
        # Create parent folder
        r = client.post(f"{API}/admin/media/folders", headers=headers, json={
            "name": f"Test_{ts}"
        })
        results.check(r.status_code == 201, "Create parent folder", f"status {r.status_code}")
        parent_folder = r.json() if r.status_code == 201 else {}
        
        # Create child folder
        r = client.post(f"{API}/admin/media/folders", headers=headers, json={
            "name": "Subfolder",
            "parent_id": parent_folder.get("id")
        })
        results.check(r.status_code == 201, "Create nested subfolder", f"status {r.status_code}")
        child_folder = r.json() if r.status_code == 201 else {}
        
        # Verify tree structure
        r = client.get(f"{API}/admin/media/folders/tree", headers=headers)
        results.check(r.status_code == 200, "GET folder tree", f"status {r.status_code}")
        
        # ========== 4. FILE UPLOAD (LOCAL STORAGE) ==========
        print("\n--- 4. File Upload (Local Storage) ---")
        
        # Upload a JPEG image
        jpeg_data = create_test_image(1200, 800, "JPEG")
        results.check(len(jpeg_data) > 10000, "Test JPEG created", f"{len(jpeg_data)//1024}KB")
        
        files = [
            ("files", ("test-product.jpg", jpeg_data, "image/jpeg")),
            ("files", ("test-banner.png", create_test_image(600, 400, "PNG"), "image/png"))
        ]
        
        r = client.post(
            f"{API}/admin/media/upload",
            headers=headers,
            files=files,
            data={"folder_id": child_folder.get("id")}
        )
        results.check(r.status_code == 201, "POST /admin/media/upload (multi-file)", f"status {r.status_code}")
        
        uploaded = []
        if r.status_code == 201:
            body = r.json()
            uploaded = body.get("uploaded", [])
            results.check(len(uploaded) == 2, "Both files uploaded", f"{len(uploaded)} files")
            results.check(not body.get("failed"), "No upload failures", str(body.get("failed", [])))
            
            if uploaded:
                first_asset = uploaded[0]
                results.check(
                    first_asset.get("url", "").startswith("/api/media/"),
                    "Image URL is LOCAL (not external)",
                    first_asset.get("url", "")[:50]
                )
                results.check(
                    first_asset.get("thumb_url", "").endswith(".webp"),
                    "WebP thumbnail generated",
                    first_asset.get("thumb_url", "")[-30:]
                )
                
                # Verify file exists on disk
                media_root = Path("/app/backend/media")
                rel_path = first_asset.get("url", "").split("/api/media/", 1)[-1]
                disk_path = media_root / rel_path
                results.check(disk_path.exists(), "File exists on local disk", str(disk_path))
        
        # ========== 5. FILE SERVING (NOT BROKEN) ==========
        print("\n--- 5. File Serving (Images Render) ---")
        
        if uploaded:
            for asset in uploaded[:2]:
                url = asset.get("url")
                if url:
                    # Test original image
                    r = client.get(f"{BASE_URL}{url}")
                    results.check(
                        r.status_code == 200 and len(r.content) > 1000,
                        f"GET {asset.get('filename')} → 200",
                        f"{len(r.content)//1024}KB"
                    )
                    
                    # Test thumbnail
                    thumb_url = asset.get("thumb_url")
                    if thumb_url:
                        r = client.get(f"{BASE_URL}{thumb_url}")
                        results.check(
                            r.status_code == 200,
                            f"Thumbnail renders",
                            f"status {r.status_code}"
                        )
        
        # ========== 6. SELF-HEAL MECHANISM ==========
        print("\n--- 6. Self-Heal (GridFS Mirror) ---")
        
        if uploaded:
            test_asset = uploaded[0]
            url = test_asset.get("url")
            rel_path = url.split("/api/media/", 1)[-1]
            disk_path = Path("/app/backend/media") / rel_path
            
            # Delete file from disk
            if disk_path.exists():
                disk_path.unlink()
                results.check(not disk_path.exists(), "File deleted from disk", "simulating loss")
                
                # Try to access - should self-heal
                r = client.get(f"{BASE_URL}{url}")
                results.check(
                    r.status_code == 200 and len(r.content) > 1000,
                    "Self-heal: file restored from GridFS",
                    f"status {r.status_code}, {len(r.content)//1024}KB"
                )
                results.check(disk_path.exists(), "File restored to disk", str(disk_path))
        
        # ========== 7. ADD FROM URL (DOWNLOADS LOCALLY) ==========
        print("\n--- 7. Add from URL (Downloads Locally) ---")
        
        external_url = "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&q=70"
        r = client.post(f"{API}/admin/media/from-url", headers=headers, json={
            "url": external_url,
            "folder_id": child_folder.get("id"),
            "alt": "Test external image"
        })
        results.check(r.status_code == 201, "POST /admin/media/from-url", f"status {r.status_code}")
        
        if r.status_code == 201:
            external_asset = r.json()
            results.check(
                external_asset.get("url", "").startswith("/api/media/"),
                "External URL downloaded to LOCAL storage",
                external_asset.get("url", "")[:50]
            )
            
            # Verify it's accessible
            r = client.get(f"{BASE_URL}{external_asset.get('url')}")
            results.check(
                r.status_code == 200 and len(r.content) > 5000,
                "Downloaded image renders",
                f"{len(r.content)//1024}KB"
            )
        
        # ========== 8. ASSET METADATA & MOVE ==========
        print("\n--- 8. Asset Metadata & Operations ---")
        
        if uploaded:
            asset_id = uploaded[0].get("id")
            old_url = uploaded[0].get("url")
            
            # Update metadata
            r = client.patch(f"{API}/admin/media/assets/{asset_id}", headers=headers, json={
                "filename": "renamed-product.jpg",
                "alt": "Product image",
                "title": "Main product photo"
            })
            results.check(r.status_code == 200, "PATCH asset metadata", f"status {r.status_code}")
            
            if r.status_code == 200:
                updated = r.json()
                results.check(
                    updated.get("url") == old_url,
                    "URL unchanged after rename (links safe)",
                    "URL stable"
                )
        
        # ========== 9. BULK OPERATIONS ==========
        print("\n--- 9. Bulk Operations ---")
        
        if len(uploaded) >= 2:
            asset_ids = [a["id"] for a in uploaded[:2]]
            
            # Bulk move
            r = client.post(f"{API}/admin/media/assets/bulk-move", headers=headers, json={
                "ids": asset_ids,
                "folder_id": parent_folder.get("id")
            })
            results.check(r.status_code == 200, "POST bulk-move", f"status {r.status_code}")
            
            # Bulk delete
            r = client.post(f"{API}/admin/media/assets/bulk-delete", headers=headers, json={
                "ids": asset_ids
            })
            results.check(
                r.status_code == 200 and r.json().get("count") == len(asset_ids),
                "POST bulk-delete",
                f"deleted {r.json().get('count', 0)} assets"
            )
        
        # ========== 10. PRODUCT INTEGRATION ==========
        print("\n--- 10. Product Integration ---")
        
        # Get a product
        r = client.get(f"{API}/admin/products?limit=1", headers=headers)
        results.check(r.status_code == 200, "GET /admin/products", f"status {r.status_code}")
        
        if r.status_code == 200:
            products = r.json()
            product_list = products.get("items") if isinstance(products, dict) else products
            
            if product_list:
                product = product_list[0]
                product_id = product["id"]
                
                # Upload image for product
                product_img = create_test_image(1000, 1000, "JPEG")
                r = client.post(
                    f"{API}/admin/media/upload",
                    headers=headers,
                    files={"file": ("product-main.jpg", product_img, "image/jpeg")}
                )
                
                if r.status_code == 201:
                    product_asset = r.json().get("uploaded", [{}])[0]
                    product_img_url = product_asset.get("url")
                    
                    # Update product with image
                    r = client.get(f"{API}/admin/products/{product_id}", headers=headers)
                    if r.status_code == 200:
                        full_product = r.json()
                        
                        # Prepare update payload
                        update_payload = {k: v for k, v in full_product.items() 
                                        if k not in ("_id", "created_at", "updated_at", "rating", "review_count")}
                        update_payload["images"] = [product_img_url]
                        
                        r = client.put(f"{API}/admin/products/{product_id}", headers=headers, json=update_payload)
                        results.check(r.status_code == 200, "Update product with media", f"status {r.status_code}")
                        
                        # Verify on public catalog
                        slug = full_product.get("slug")
                        r = client.get(f"{API}/products/{slug}")
                        if r.status_code == 200:
                            public_product = r.json()
                            results.check(
                                product_img_url in (public_product.get("images") or []),
                                "Product image visible on storefront",
                                "image in catalog"
                            )
        
        # ========== 11. SECURITY & VALIDATION ==========
        print("\n--- 11. Security & Validation ---")
        
        # Test file size limit
        huge_file = b"\xff\xd8\xff" + os.urandom(16 * 1024 * 1024)  # >15MB
        r = client.post(
            f"{API}/admin/media/upload",
            headers=headers,
            files={"file": ("huge.jpg", huge_file, "image/jpeg")}
        )
        results.check(r.status_code == 400, "Reject file >15MB", f"status {r.status_code}")
        
        # Test invalid mime type
        r = client.post(
            f"{API}/admin/media/upload",
            headers=headers,
            files={"file": ("virus.exe", b"MZ\x90\x00", "application/x-msdownload")}
        )
        results.check(r.status_code == 400, "Reject non-image mime", f"status {r.status_code}")
        
        # Test path traversal
        r = client.get(f"{BASE_URL}/api/media/../../../etc/passwd")
        results.check(r.status_code in (400, 404), "Block path traversal", f"status {r.status_code}")
        
        # Test RBAC - no auth
        r = client.get(f"{API}/admin/media/assets")
        results.check(r.status_code == 401, "Require authentication", f"status {r.status_code}")
        
        # Test RBAC - customer role
        r = client.post(f"{API}/auth/login", json={
            "email": CUSTOMER_EMAIL,
            "password": CUSTOMER_PASSWORD
        })
        if r.status_code == 200:
            customer_token = r.json().get("token")
            r = client.get(f"{API}/admin/media/assets", headers={"Authorization": f"Bearer {customer_token}"})
            results.check(r.status_code == 403, "Block customer from admin media", f"status {r.status_code}")
        
        # ========== 12. LEGACY COMPATIBILITY ==========
        print("\n--- 12. Legacy Compatibility ---")
        
        r = client.get(f"{API}/admin/uploads", headers=headers)
        results.check(r.status_code == 200, "GET /admin/uploads (legacy)", f"status {r.status_code}")
        
        r = client.post(
            f"{API}/admin/uploads",
            headers=headers,
            files={"file": ("legacy.png", create_test_image(200, 200, "PNG"), "image/png")}
        )
        results.check(r.status_code == 200, "POST /admin/uploads (legacy)", f"status {r.status_code}")
        
        # ========== CLEANUP ==========
        print("\n--- Cleanup ---")
        
        # Delete test folder (cascade)
        if parent_folder.get("id"):
            r = client.delete(f"{API}/admin/media/folders/{parent_folder['id']}?cascade=true", headers=headers)
            results.check(r.status_code == 200, "Cleanup test folder", f"status {r.status_code}")
    
    return results.summary()


if __name__ == "__main__":
    sys.exit(main())
