"""Tests for Storefront CMS (E9 extended: seo, home_layout, gallery, pages)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://parfum-vault-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@collectorparfum.id"
ADMIN_PASS = "Admin#2026"

EXPECTED_KEYS = [
    "announcement", "header", "footer", "seo", "home_layout",
    "hero", "marquee_words", "story_strip", "occasion_section", "character_section",
    "trending", "media_editorial", "featured", "big_word", "new_arrivals",
    "gallery", "video", "testimonials", "faq", "trust",
    "shop_page", "locations_page", "voucher_page", "about", "contact",
]


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def hdr(token):
    return {"Authorization": f"Bearer {token}"}


# -------- GET /api/content ---------
def test_public_content_has_all_keys():
    r = requests.get(f"{API}/content", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    missing = [k for k in EXPECTED_KEYS if k not in data]
    assert not missing, f"missing keys: {missing}"
    assert "category_section" not in data, "category_section should be removed"
    # home_layout sections has 15 items
    hl = data["home_layout"]
    assert "sections" in hl and isinstance(hl["sections"], list)
    assert len(hl["sections"]) == 15
    for row in hl["sections"]:
        assert "key" in row and "visible" in row


# -------- GET /api/admin/content/schema ---------
def test_admin_schema_defaults_and_types(hdr):
    r = requests.get(f"{API}/admin/content/schema", headers=hdr, timeout=15)
    assert r.status_code == 200, r.text
    schema = r.json()
    assert isinstance(schema, list)
    by_key = {s["key"]: s for s in schema}
    for k in EXPECTED_KEYS:
        assert k in by_key, f"schema missing {k}"
        assert "default" in by_key[k], f"{k} default missing"

    # home_layout has sections repeater with select key (15 opts) + toggle visible
    hl = by_key["home_layout"]
    fields = {f["name"]: f for f in hl["fields"]}
    assert fields["sections"]["type"] == "repeater"
    sub = {f["name"]: f for f in fields["sections"]["item"]}
    assert sub["key"]["type"] == "select"
    assert len(sub["key"]["options"]) == 15
    assert sub["visible"]["type"] == "toggle"

    # gallery has gallery + select layout
    g = by_key["gallery"]
    gfields = {f["name"]: f for f in g["fields"]}
    assert gfields["items"]["type"] == "gallery"
    assert gfields["layout"]["type"] == "select"


# -------- Coerce: gallery ---------
def test_coerce_gallery(hdr):
    payload = {"data": {
        "layout": "bogus",
        "items": [
            {"image": "/api/media/a.jpg", "caption": "A"},
            "https://x.com/b.jpg",
            "",
            {"caption": "tanpa gambar"},
        ],
    }}
    r = requests.put(f"{API}/admin/content/gallery", headers=hdr, json=payload, timeout=15)
    assert r.status_code == 200, r.text
    g = requests.get(f"{API}/content", timeout=15).json()["gallery"]
    assert g["layout"] == "", f"expected empty layout got {g['layout']!r}"
    assert len(g["items"]) == 2, f"expected 2 items got {g['items']}"
    assert g["items"][0]["image"] == "/api/media/a.jpg"
    assert g["items"][0]["caption"] == "A"
    assert g["items"][1]["image"] == "https://x.com/b.jpg"
    assert g["items"][1]["caption"] == ""


# -------- Coerce: home_layout ---------
def test_coerce_home_layout(hdr):
    payload = {"data": {"sections": [
        {"key": "hero", "visible": "true"},
        {"key": "nope", "visible": False},
        {"key": "faq", "visible": 0},
    ]}}
    r = requests.put(f"{API}/admin/content/home_layout", headers=hdr, json=payload, timeout=15)
    assert r.status_code == 200, r.text
    hl = requests.get(f"{API}/content", timeout=15).json()["home_layout"]
    secs = hl["sections"]
    # Note: PUT merges — sections is fully replaced by coerce since it's an array field
    # After update, first 3 items reflect our payload
    assert secs[0]["key"] == "hero" and secs[0]["visible"] is True
    assert secs[1]["key"] == "" and secs[1]["visible"] is False
    assert secs[2]["key"] == "faq" and secs[2]["visible"] is False


# -------- Revert both ---------
def test_revert_gallery_and_home_layout(hdr):
    r1 = requests.post(f"{API}/admin/content/gallery/revert", headers=hdr, json={"to_default": True}, timeout=15)
    assert r1.status_code == 200, r1.text
    r2 = requests.post(f"{API}/admin/content/home_layout/revert", headers=hdr, json={"to_default": True}, timeout=15)
    assert r2.status_code == 200, r2.text
    data = requests.get(f"{API}/content", timeout=15).json()
    assert data["gallery"]["items"] == []
    assert data["gallery"]["layout"] == "masonry"
    assert len(data["home_layout"]["sections"]) == 15
    # gallery visible=False by default
    gallery_row = next(s for s in data["home_layout"]["sections"] if s["key"] == "gallery")
    assert gallery_row["visible"] is False


# -------- shop_page update + revert ---------
def test_shop_page_update_and_revert(hdr):
    r = requests.put(f"{API}/admin/content/shop_page", headers=hdr,
                     json={"data": {"title": "Uji CMS Toko"}}, timeout=15)
    assert r.status_code == 200, r.text
    data = requests.get(f"{API}/content", timeout=15).json()
    assert data["shop_page"]["title"] == "Uji CMS Toko"
    rv = requests.post(f"{API}/admin/content/shop_page/revert", headers=hdr,
                       json={"to_default": True}, timeout=15)
    assert rv.status_code == 200
    data2 = requests.get(f"{API}/content", timeout=15).json()
    assert data2["shop_page"]["title"] == "Semua parfum, satu"
