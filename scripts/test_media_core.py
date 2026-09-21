"""test_media_core.py — POC INTI Media Manager lokal (E20).

Membuktikan seluruh jalur kritis media SEBELUM UI dibangun:

  1  login admin
  2  folder bertingkat: create (3 level) + tree + rename + pindah + guard siklus
  3  upload multi-berkas (JPEG besar >5MB, PNG transparan, SVG, GIF animasi, HEIC-like)
  4  optimasi Pillow: EXIF auto-orient, batas 2400px, turunan WebP 400/1000
  5  penyajian HTTP: GET /api/media/... -> 200 + content-type + byte>0 (asli, thumb, medium)
  6  SELF-HEAL: hapus berkas dari disk -> GET tetap 200 + berkas kembali ada
  7  from-url: unduh gambar eksternal -> tersimpan LOKAL + tampil 200
  8  patch aset: rename, alt/title, pindah folder (URL TIDAK berubah)
  9  daftar aset: cari + filter + sort + paginasi + X-Total-Count
  10 bulk move + bulk delete (berkas & mirror ikut terhapus)
  11 hapus folder: isi dipindahkan ke induk (tanpa orphan) + cascade
  12 pasang media ke produk lalu verifikasi lewat endpoint katalog PUBLIK
  13 penolakan: mime tidak didukung + >15MB + traversal -> 400/404, TANPA 5xx
  14 kompatibilitas legacy: /admin/uploads (GET/POST), /admin/media (GET/POST/DELETE),
     berkas datar lama backend/media/*.png tetap 200

Jalankan: cd /app && python scripts/test_media_core.py
"""
import io
import os
import random
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

BASE = os.environ.get("BASE_URL", "http://localhost:8001")
API = f"{BASE}/api"
ADMIN = {"email": os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id"),
         "password": os.environ.get("ADMIN_PASSWORD", "Admin#2026")}
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/app/backend/media"))

G, R, Y, C, X = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[0m"
PASS, FAIL, NOTES = [], [], []


def ok(name, extra=""):
    PASS.append(name)
    print(f"  {G}✓{X} {name}" + (f" {Y}({extra}){X}" if extra else ""))


def bad(name, detail=""):
    FAIL.append((name, detail))
    print(f"  {R}✗{X} {name} — {detail}")


def check(cond, name, detail=""):
    if cond:
        ok(name, detail if cond is True and detail else "")
    else:
        bad(name, detail or "kondisi tidak terpenuhi")
    return bool(cond)


def head(title):
    print(f"\n{C}── {title}{X}")


# ============================== fixtures gambar ==============================
def jpeg_bytes(w=1200, h=800, noise=False, exif_orientation=None, quality=90):
    im = Image.new("RGB", (w, h))
    px = im.load()
    if noise:
        rnd = random.Random(42)
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                c = (rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255))
                px[x, y] = c
                if x + 1 < w:
                    px[x + 1, y] = c
                if y + 1 < h:
                    px[x, y + 1] = c
                if x + 1 < w and y + 1 < h:
                    px[x + 1, y + 1] = c
    else:
        for y in range(h):
            for x in range(0, w, 40):
                px[x, y] = (x % 255, y % 255, 120)
    buf = io.BytesIO()
    kwargs = {"quality": quality, "optimize": False}
    if exif_orientation:
        exif = im.getexif()
        exif[274] = exif_orientation  # 274 = Orientation
        kwargs["exif"] = exif.tobytes()
    im.save(buf, "JPEG", **kwargs)
    return buf.getvalue()


def big_jpeg(target_mb=7):
    """JPEG valid berukuran > target_mb (membuktikan batas lama 5MB sudah naik)."""
    w, h = 3000, 2200
    while True:
        data = jpeg_bytes(w, h, noise=True, quality=97)
        if len(data) >= target_mb * 1024 * 1024 or w > 8000:
            return data
        w, h = int(w * 1.25), int(h * 1.25)


def png_bytes(w=600, h=600):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if (x // 30 + y // 30) % 2 == 0:
                px[x, y] = (200, 40, 90, 255)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def svg_bytes():
    return (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            b'<circle cx="50" cy="50" r="40" fill="#c9a227"/></svg>')


def gif_bytes():
    frames = []
    for i in range(4):
        im = Image.new("P", (240, 240))
        px = im.load()
        for y in range(240):
            for x in range(240):
                px[x, y] = (x + y + i * 30) % 256
        frames.append(im)
    buf = io.BytesIO()
    frames[0].save(buf, "GIF", save_all=True, append_images=frames[1:], duration=120,
                   loop=0)
    return buf.getvalue()


def heic_bytes():
    """HEIC asli bila pillow-heif tersedia, kalau tidak None (skip)."""
    try:
        import pillow_heif
        im = Image.new("RGB", (900, 700), (30, 30, 40))
        px = im.load()
        for y in range(0, 700, 3):
            for x in range(0, 900, 3):
                px[x, y] = (x % 255, y % 255, 90)
        buf = io.BytesIO()
        pillow_heif.from_pillow(im).save(buf, format="HEIF", quality=80)
        return buf.getvalue()
    except Exception as e:  # pragma: no cover
        NOTES.append(f"fixture HEIC gagal dibuat: {type(e).__name__} {e}")
        return None


def avif_bytes():
    try:
        im = Image.new("RGB", (800, 600), (10, 90, 120))
        buf = io.BytesIO()
        im.save(buf, "AVIF", quality=70)
        return buf.getvalue()
    except Exception:
        return None


# ============================== helpers HTTP ==============================
class Api:
    def __init__(self, client, token=None):
        self.c = client
        self.token = token

    def h(self, extra=None):
        d = {}
        if self.token:
            d["Authorization"] = f"Bearer {self.token}"
        if extra:
            d.update(extra)
        return d

    def get(self, path, **kw):
        return self.c.get(f"{API}{path}", headers=self.h(), **kw)

    def post(self, path, **kw):
        return self.c.post(f"{API}{path}", headers=self.h(), **kw)

    def patch(self, path, **kw):
        return self.c.patch(f"{API}{path}", headers=self.h(), **kw)

    def put(self, path, **kw):
        return self.c.put(f"{API}{path}", headers=self.h(), **kw)

    def delete(self, path, **kw):
        return self.c.delete(f"{API}{path}", headers=self.h(), **kw)

    def raw(self, url_path):
        return self.c.get(f"{BASE}{url_path}")


def rel_of(url: str) -> str:
    return url.split("/api/media/", 1)[-1] if "/api/media/" in url else ""


def disk_path(url: str) -> Path:
    return MEDIA_ROOT / rel_of(url)


# ============================== TESTS ==============================
def main():
    random.seed(7)
    with httpx.Client(timeout=120.0) as client:
        # ---------- 1. LOGIN ----------
        head("1. Login admin")
        r = client.post(f"{API}/auth/login", json=ADMIN)
        if r.status_code != 200:
            print(f"{R}FATAL: login gagal ({r.status_code}) {r.text[:200]}{X}")
            print(f"{Y}Jalankan dulu: python scripts/seed_data.py{X}")
            return 1
        api = Api(client, r.json().get("token"))
        ok("login admin", f"token {str(api.token)[:14]}…")

        st = api.get("/admin/media/stats")
        check(st.status_code == 200, "GET /admin/media/stats", str(st.status_code))
        stats0 = st.json() if st.status_code == 200 else {}
        NOTES.append(f"stats awal: {stats0}")
        check(int(stats0.get("max_mb", 0)) >= 15, "batas upload >= 15 MB",
              f"max_mb={stats0.get('max_mb')}")
        check(stats0.get("mirror") is True, "mirror MongoDB aktif (self-heal siap)",
              f"mirror={stats0.get('mirror')}")

        # ---------- 2. FOLDER BERTINGKAT ----------
        head("2. Folder bertingkat (nested)")
        ts = str(int(time.time()))
        r = api.post("/admin/media/folders", json={"name": f"POC {ts}"})
        check(r.status_code == 201, "buat folder level-1", str(r.status_code))
        f1 = r.json() if r.status_code == 201 else {}
        r = api.post("/admin/media/folders", json={"name": "Banner", "parent_id": f1.get("id")})
        check(r.status_code == 201, "buat folder level-2", str(r.status_code))
        f2 = r.json() if r.status_code == 201 else {}
        r = api.post("/admin/media/folders", json={"name": "2026", "parent_id": f2.get("id")})
        check(r.status_code == 201, "buat folder level-3", str(r.status_code))
        f3 = r.json() if r.status_code == 201 else {}
        check(f3.get("depth") == 3 and f3.get("path", "").endswith("/Banner/2026"),
              "path & depth folder level-3 benar", f3.get("path"))

        r = api.post("/admin/media/folders", json={"name": "Banner", "parent_id": f1.get("id")})
        check(r.status_code == 400, "folder duplikat ditolak 400", str(r.status_code))

        r = api.get("/admin/media/folders/tree")
        tree = r.json() if r.status_code == 200 else {}
        node = next((n for n in tree.get("tree", []) if n["id"] == f1.get("id")), None)
        check(node is not None and node["children"] and node["children"][0]["children"],
              "tree bertingkat 3 level terbentuk")

        r = api.patch(f"/admin/media/folders/{f2['id']}", json={"name": "Banner Utama"})
        check(r.status_code == 200 and r.json().get("name") == "Banner Utama",
              "rename folder", str(r.status_code))
        r = api.get("/admin/media/folders")
        f3b = next((x for x in r.json().get("folders", []) if x["id"] == f3.get("id")), {})
        check(f3b.get("path", "").endswith("/Banner Utama/2026"),
              "path keturunan ikut diperbarui setelah rename", f3b.get("path"))

        r = api.patch(f"/admin/media/folders/{f1['id']}",
                      json={"parent_id": f3.get("id"), "move": True})
        check(r.status_code == 400, "guard siklus folder (induk=keturunan) -> 400",
              str(r.status_code))

        # ---------- 3+4. UPLOAD MULTI + OPTIMASI ----------
        head("3+4. Upload multi-berkas + optimasi Pillow")
        big = big_jpeg(7)
        check(len(big) > 5 * 1024 * 1024, "fixture JPEG > 5MB dibuat",
              f"{len(big)/1024/1024:.1f} MB")
        files = [
            ("files", ("foto-besar.jpg", big, "image/jpeg")),
            ("files", ("transparan.png", png_bytes(), "image/png")),
            ("files", ("ikon.svg", svg_bytes(), "image/svg+xml")),
            ("files", ("animasi.gif", gif_bytes(), "image/gif")),
        ]
        hb = heic_bytes()
        if hb:
            files.append(("files", ("iphone.heic", hb, "image/heic")))
        ab = avif_bytes()
        if ab:
            files.append(("files", ("modern.avif", ab, "image/avif")))
        r = api.post("/admin/media/upload", files=files,
                     data={"folder_id": f3.get("id")})
        check(r.status_code == 201, "POST /admin/media/upload (multi)", str(r.status_code))
        body = r.json() if r.status_code == 201 else {"uploaded": [], "failed": []}
        up = body.get("uploaded", [])
        check(not body.get("failed"), "tidak ada berkas gagal", str(body.get("failed"))[:200])
        check(len(up) == len(files), f"semua {len(files)} berkas tersimpan",
              f"{len(up)} sukses")
        by_name = {a["filename"]: a for a in up}

        jpg = by_name.get("foto-besar.jpg", {})
        check(jpg.get("width") and max(jpg["width"], jpg["height"] or 0) <= 2400,
              "sisi terpanjang dibatasi 2400px", f"{jpg.get('width')}x{jpg.get('height')}")
        check(jpg.get("size", 0) < len(big), "berkas JPEG dioptimasi (lebih kecil)",
              f"{len(big)//1024}KB -> {jpg.get('size', 0)//1024}KB")
        check(jpg.get("thumb_url", "").endswith("_400.webp"), "thumbnail WebP 400 dibuat",
              jpg.get("thumb_url"))
        check(jpg.get("medium_url", "").endswith("_1000.webp"), "turunan WebP 1000 dibuat",
              jpg.get("medium_url"))
        check(jpg.get("folder_id") == f3.get("id"), "aset masuk ke folder yang dipilih")

        pngd = by_name.get("transparan.png", {})
        check(pngd.get("mime") == "image/png", "PNG tetap PNG (transparansi terjaga)",
              pngd.get("mime"))
        svg = by_name.get("ikon.svg", {})
        check(svg.get("mime") == "image/svg+xml" and svg.get("url", "").endswith(".svg"),
              "SVG disimpan apa adanya", svg.get("url"))
        gif = by_name.get("animasi.gif", {})
        check(gif.get("url", "").endswith(".gif"), "GIF animasi tidak dikonversi",
              gif.get("url"))
        check(gif.get("thumb_url", "").endswith(".webp"), "GIF punya thumbnail statis")
        if hb:
            heic = by_name.get("iphone.heic", {})
            check(heic.get("mime") == "image/jpeg" and heic.get("url", "").endswith(".jpg"),
                  "HEIC iPhone dikonversi ke JPEG", heic.get("url"))
        else:
            NOTES.append("HEIC dilewati: pillow-heif tidak tersedia")
        if ab:
            av = by_name.get("modern.avif", {})
            check(av.get("width") == 800, "AVIF diproses", av.get("mime"))

        # EXIF auto-orient: gambar 1200x800 dengan orientation=6 harus jadi 800x1200
        r = api.post("/admin/media/upload",
                     files={"file": ("exif.jpg", jpeg_bytes(1200, 800, exif_orientation=6),
                                     "image/jpeg")},
                     data={"folder_id": f3.get("id")})
        ex = (r.json().get("uploaded") or [{}])[0] if r.status_code == 201 else {}
        check(ex.get("width") == 800 and ex.get("height") == 1200,
              "EXIF orientation diterapkan (auto-rotate)",
              f"{ex.get('width')}x{ex.get('height')}")

        # De-dup: unggah berkas identik -> dipakai ulang
        r = api.post("/admin/media/upload",
                     files={"file": ("transparan-2.png", png_bytes(), "image/png")})
        dedup = (r.json().get("uploaded") or [{}])[0] if r.status_code == 201 else {}
        check(dedup.get("id") == pngd.get("id"), "berkas identik di-dedup (hemat disk)",
              f"id={dedup.get('id')}")

        # ---------- 5. PENYAJIAN HTTP ----------
        head("5. Penyajian berkas via HTTP")
        for label, url, want in (
            ("asli", jpg.get("url"), "image/jpeg"),
            ("thumb", jpg.get("thumb_url"), "image/webp"),
            ("medium", jpg.get("medium_url"), "image/webp"),
            ("svg", svg.get("url"), "image/svg+xml"),
            ("gif", gif.get("url"), "image/gif"),
            ("png", pngd.get("url"), "image/png"),
        ):
            if not url:
                bad(f"GET {label}", "url kosong")
                continue
            rr = api.raw(url)
            ctype = rr.headers.get("content-type", "").split(";")[0]
            check(rr.status_code == 200 and ctype == want and len(rr.content) > 0,
                  f"GET {label} -> 200 {want}",
                  f"{rr.status_code} {ctype} {len(rr.content)}B")
        rr = api.raw(jpg.get("url", ""))
        check("max-age" in (rr.headers.get("cache-control") or ""),
              "header cache aktif", rr.headers.get("cache-control"))
        etag = rr.headers.get("etag")
        if etag:
            r304 = client.get(f"{BASE}{jpg['url']}", headers={"If-None-Match": etag})
            check(r304.status_code == 304, "ETag 304 Not Modified", str(r304.status_code))

        # ---------- 6. SELF-HEAL ----------
        head("6. Self-heal (berkas hilang dari disk)")
        p = disk_path(jpg.get("url", ""))
        check(p.exists(), "berkas ada di disk lokal", str(p))
        pt = disk_path(jpg.get("thumb_url", ""))
        try:
            p.unlink()
            pt.unlink()
        except Exception as e:
            bad("hapus berkas dari disk (simulasi rebuild)", str(e))
        check(not p.exists(), "berkas benar-benar terhapus dari disk")
        rr = api.raw(jpg["url"])
        check(rr.status_code == 200 and len(rr.content) > 0,
              "GET setelah berkas hilang -> TETAP 200 (self-heal)",
              f"{rr.status_code} {len(rr.content)}B")
        check(p.exists(), "berkas dipulihkan otomatis ke disk")
        rr = api.raw(jpg["thumb_url"])
        check(rr.status_code == 200, "thumbnail juga ter-self-heal", str(rr.status_code))

        # ---------- 7. FROM URL ----------
        head("7. Tambah dari URL eksternal -> disimpan LOKAL")
        ext_url = ("https://images.unsplash.com/photo-1594035910387-fea47794261f"
                   "?w=1200&q=80")
        r = api.post("/admin/media/from-url",
                     json={"url": ext_url, "folder_id": f2.get("id"),
                           "alt": "Flatlay parfum"})
        if r.status_code == 201:
            ing = r.json()
            check(ing.get("url", "").startswith("/api/media/"),
                  "URL eksternal diunduh & disimpan lokal", ing.get("url"))
            check(disk_path(ing["url"]).exists(), "berkas hasil unduhan ada di disk")
            rr = api.raw(ing["url"])
            check(rr.status_code == 200 and len(rr.content) > 1000,
                  "gambar hasil unduhan tampil 200", f"{rr.status_code} {len(rr.content)}B")
            check(ing.get("alt") == "Flatlay parfum", "alt text tersimpan")
        else:
            bad("POST /admin/media/from-url", f"{r.status_code} {r.text[:200]}")
            ing = {}
        r = api.post("/admin/media/from-url", json={"url": "bukan-url"})
        check(r.status_code == 400, "URL tidak valid ditolak 400", str(r.status_code))
        r = api.post("/admin/media/from-url",
                     json={"url": "https://example.com/tidak-ada-gambar.txt"})
        check(r.status_code == 400, "URL non-gambar ditolak 400", str(r.status_code))

        # ---------- 8. PATCH ASET ----------
        head("8. Ubah metadata aset (URL tetap)")
        old_url = pngd.get("url")
        r = api.patch(f"/admin/media/assets/{pngd['id']}",
                      json={"filename": "banner-utama.png", "alt": "Banner utama",
                            "title": "Banner", "tags": ["banner", "home"],
                            "folder_id": f2.get("id"), "move": True})
        pat = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200, "PATCH aset", str(r.status_code))
        check(pat.get("filename") == "banner-utama.png", "rename nama tampilan")
        check(pat.get("alt") == "Banner utama" and pat.get("title") == "Banner",
              "alt & title tersimpan")
        check(pat.get("tags") == ["banner", "home"], "tags tersimpan", str(pat.get("tags")))
        check(pat.get("folder_id") == f2.get("id"), "pindah folder")
        check(pat.get("url") == old_url, "URL TIDAK berubah setelah rename (link aman)")
        rr = api.raw(pat.get("url", ""))
        check(rr.status_code == 200, "berkas masih tersaji setelah rename")

        # replace berkas: URL tetap sama, biner berubah
        r = api.post(f"/admin/media/assets/{pngd['id']}/replace",
                     files={"file": ("baru.png", png_bytes(400, 400), "image/png")})
        rep = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200, "POST replace berkas", str(r.status_code))
        check(rep.get("url") == old_url, "URL tetap sama setelah replace")
        check(rep.get("width") == 400, "dimensi terbarui setelah replace",
              f"{rep.get('width')}")

        # ---------- 9. LIST / CARI / SORT / PAGINASI ----------
        head("9. Daftar aset: cari, filter, sort, paginasi")
        r = api.get(f"/admin/media/assets?folder_id={f3['id']}&limit=50")
        check(r.status_code == 200, "GET /admin/media/assets", str(r.status_code))
        lst = r.json() if r.status_code == 200 else {}
        check(r.headers.get("X-Total-Count") is not None, "header X-Total-Count ada",
              r.headers.get("X-Total-Count"))
        check(lst.get("total", 0) >= 4, "aset folder terhitung", f"total={lst.get('total')}")
        r = api.get(f"/admin/media/assets?folder_id={f1['id']}&recursive=true&limit=100")
        check(r.json().get("total", 0) >= lst.get("total", 0),
              "recursive=true menghitung subfolder",
              f"{r.json().get('total')} >= {lst.get('total')}")
        r = api.get("/admin/media/assets?q=animasi&limit=10")
        check(any("animasi" in (a["filename"] or "") for a in r.json().get("items", [])),
              "pencarian nama berkas")
        r = api.get(f"/admin/media/assets?folder_id={f3['id']}&sort=largest&limit=5")
        items = r.json().get("items", [])
        sizes = [a["size"] for a in items]
        check(sizes == sorted(sizes, reverse=True), "sort=largest berurutan", str(sizes))
        r = api.get(f"/admin/media/assets?folder_id={f3['id']}&sort=name&limit=2&page=1")
        p1 = [a["id"] for a in r.json().get("items", [])]
        r = api.get(f"/admin/media/assets?folder_id={f3['id']}&sort=name&limit=2&page=2")
        p2 = [a["id"] for a in r.json().get("items", [])]
        check(len(p1) == 2 and not set(p1) & set(p2), "paginasi tidak tumpang tindih",
              f"{p1} vs {p2}")
        r = api.get("/admin/media/assets?kind=external&limit=5")
        check(r.status_code == 200, "filter kind=external", str(r.status_code))

        # ---------- 10. BULK ----------
        head("10. Aksi massal (bulk move & bulk delete)")
        r = api.post("/admin/media/upload", files=[
            ("files", ("bulk-a.png", png_bytes(120, 120), "image/png")),
            ("files", ("bulk-b.png", png_bytes(130, 130), "image/png")),
            ("files", ("bulk-c.png", png_bytes(140, 140), "image/png")),
        ], data={"folder_id": f3.get("id")})
        bulk = r.json().get("uploaded", []) if r.status_code == 201 else []
        check(len(bulk) == 3, "3 berkas untuk uji bulk", str(len(bulk)))
        ids = [a["id"] for a in bulk]
        r = api.post("/admin/media/assets/bulk-move",
                     json={"ids": ids, "folder_id": f2.get("id")})
        check(r.status_code == 200 and r.json().get("moved") == 3, "bulk-move 3 aset",
              str(r.json()))
        r = api.get(f"/admin/media/assets?folder_id={f2['id']}&limit=50")
        moved_ids = {a["id"] for a in r.json().get("items", [])}
        check(set(ids) <= moved_ids, "aset benar-benar berada di folder tujuan")
        paths = [disk_path(a["url"]) for a in bulk]
        r = api.post("/admin/media/assets/bulk-delete", json={"ids": ids})
        check(r.status_code == 200 and r.json().get("count") == 3, "bulk-delete 3 aset",
              str(r.json()))
        check(all(not p.exists() for p in paths), "berkas fisik ikut terhapus")
        rr = api.raw(bulk[0]["url"])
        check(rr.status_code == 404, "URL aset terhapus -> 404 (mirror ikut bersih)",
              str(rr.status_code))

        # ---------- 11. HAPUS FOLDER ----------
        head("11. Hapus folder (aman & cascade)")
        r = api.get(f"/admin/media/assets?folder_id={f3['id']}&limit=100")
        n_before = r.json().get("total", 0)
        r = api.delete(f"/admin/media/folders/{f3['id']}")
        check(r.status_code == 200 and r.json().get("moved_assets") == n_before,
              "hapus folder -> isi dipindah ke induk (tanpa orphan)", str(r.json()))
        r = api.get(f"/admin/media/assets?folder_id={f2['id']}&limit=100")
        check(r.json().get("total", 0) >= n_before, "isi folder muncul di induk",
              f"total={r.json().get('total')}")
        r = api.post("/admin/media/folders", json={"name": "Cascade", "parent_id": f2["id"]})
        fc = r.json()
        r = api.post("/admin/media/upload",
                     files={"file": ("cascade.png", png_bytes(90, 90), "image/png")},
                     data={"folder_id": fc["id"]})
        casset = (r.json().get("uploaded") or [{}])[0]
        cpath = disk_path(casset.get("url", ""))
        r = api.delete(f"/admin/media/folders/{fc['id']}?cascade=true")
        check(r.status_code == 200 and r.json().get("cascade") is True,
              "hapus folder cascade=true", str(r.json()))
        check(not cpath.exists(), "berkas di dalam folder cascade ikut terhapus")
        r = api.delete("/admin/media/folders/mdf_tidakada")
        check(r.status_code == 404, "hapus folder tidak ada -> 404", str(r.status_code))

        # ---------- 12. PASANG KE PRODUK -> STOREFRONT ----------
        head("12. Pasang media ke produk & verifikasi di katalog publik")
        r = api.get("/admin/products?limit=1")
        plist = r.json()
        prod = (plist.get("items") if isinstance(plist, dict) else plist) or []
        if not prod:
            bad("ambil produk", "katalog kosong — jalankan seed_data.py")
        else:
            pid = prod[0]["id"]
            r = api.get(f"/admin/products/{pid}")
            full = r.json()
            r = api.post("/admin/media/upload",
                         files={"file": ("produk-hero.jpg",
                                         jpeg_bytes(1400, 1400), "image/jpeg")},
                         data={"folder_id": f2.get("id")})
            pm = (r.json().get("uploaded") or [{}])[0]
            check(bool(pm.get("url")), "upload gambar produk", pm.get("url"))
            payload = dict(full)
            for k in ("_id", "created_at", "updated_at", "rating", "review_count"):
                payload.pop(k, None)
            payload["images"] = [pm["url"]] + [
                u for u in (full.get("images") or []) if u != pm["url"]
            ][:3]
            r = api.put(f"/admin/products/{pid}", json=payload)
            check(r.status_code == 200, "PUT produk dengan gambar media lokal",
                  f"{r.status_code} {r.text[:160]}")
            slug = full.get("slug")
            rr = client.get(f"{API}/products/{slug}")
            imgs = (rr.json() or {}).get("images") or []
            check(rr.status_code == 200 and pm["url"] in imgs,
                  "gambar tampil di endpoint katalog PUBLIK", str(imgs)[:120])
            rr2 = api.raw(pm["url"])
            check(rr2.status_code == 200, "gambar produk dapat diakses tanpa login",
                  str(rr2.status_code))
            # sanity: anonim (tanpa Authorization) juga bisa
            anon = httpx.Client(timeout=30.0)
            ra = anon.get(f"{BASE}{pm['url']}")
            check(ra.status_code == 200, "akses anonim ke berkas media 200",
                  str(ra.status_code))
            anon.close()

        # ---------- 13. PENOLAKAN / KEAMANAN ----------
        head("13. Penolakan input buruk (tanpa 5xx)")
        r = api.post("/admin/media/upload",
                     files={"file": ("virus.exe", b"MZ\x90\x00" * 100,
                                     "application/x-msdownload")})
        check(r.status_code == 400, "mime tidak didukung -> 400", str(r.status_code))
        r = api.post("/admin/media/upload",
                     files={"file": ("palsu.jpg", b"bukan gambar sama sekali",
                                     "image/jpeg")})
        check(r.status_code == 400, "berkas rusak berlabel jpg -> 400", str(r.status_code))
        r = api.post("/admin/media/upload",
                     files={"file": ("raksasa.jpg", b"\xff\xd8\xff" + os.urandom(16 * 1024 * 1024),
                                     "image/jpeg")})
        check(r.status_code == 400 and "MB" in r.text, "berkas > 15MB -> 400",
              f"{r.status_code} {r.text[:80]}")
        r = api.post("/admin/media/upload", files=[])
        check(r.status_code in (400, 422), "upload tanpa berkas -> 400/422",
              str(r.status_code))
        for bad_path in ("../../../etc/passwd", "..%2f..%2fetc%2fpasswd",
                         "originals/../../server.py"):
            rr = client.get(f"{BASE}/api/media/{bad_path}")
            check(rr.status_code in (400, 404), f"path traversal '{bad_path[:22]}' ditolak",
                  str(rr.status_code))
        r = api.post("/admin/media/folders", json={"name": ""})
        check(r.status_code in (400, 422), "nama folder kosong ditolak", str(r.status_code))
        r = api.post("/admin/media/folders", json={"name": "X", "parent_id": "mdf_hantu"})
        check(r.status_code == 400, "parent_id tidak ada -> 400", str(r.status_code))
        r = api.patch("/admin/media/assets/med_hantu", json={"alt": "x"})
        check(r.status_code == 404, "PATCH aset tidak ada -> 404", str(r.status_code))
        noauth = httpx.Client(timeout=30.0)
        rr = noauth.get(f"{API}/admin/media/assets")
        check(rr.status_code == 401, "tanpa token -> 401 (RBAC)", str(rr.status_code))
        rc = noauth.post(f"{API}/auth/login",
                         json={"email": "customer@collectorparfum.id",
                               "password": "Customer#2026"})
        if rc.status_code == 200:
            ctok = rc.json().get("token")
            rr = noauth.get(f"{API}/admin/media/assets",
                            headers={"Authorization": f"Bearer {ctok}"})
            check(rr.status_code == 403, "customer -> 403 (RBAC)", str(rr.status_code))
        else:
            NOTES.append("login customer dilewati (kredensial berbeda)")
        noauth.close()

        # ---------- 14. LEGACY ----------
        head("14. Kompatibilitas legacy")
        r = api.get("/admin/uploads")
        check(r.status_code == 200 and isinstance(r.json(), list),
              "GET /admin/uploads (list) tetap jalan", str(r.status_code))
        r = api.post("/admin/uploads",
                     files={"file": ("legacy.png", png_bytes(150, 150), "image/png")})
        leg = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200 and leg.get("url", "").startswith("/api/media/"),
              "POST /admin/uploads (upload tunggal) tetap jalan",
              f"{r.status_code} {leg.get('url')}")
        rr = api.raw(leg.get("url", ""))
        check(rr.status_code == 200, "berkas legacy upload tersaji", str(rr.status_code))
        r = api.get("/admin/media")
        check(r.status_code == 200 and isinstance(r.json(), list),
              "GET /admin/media (legacy list) tetap jalan", str(r.status_code))
        r = api.post("/admin/media", json={"kind": "image", "url": ext_url,
                                           "alt": "legacy add"})
        legadd = r.json() if r.status_code in (200, 201) else {}
        check(r.status_code in (200, 201), "POST /admin/media (legacy add) tetap jalan",
              str(r.status_code))
        check(legadd.get("url", "").startswith("/api/media/"),
              "legacy add sekarang MENGUNDUH ke lokal (anti broken)", legadd.get("url"))
        r = api.post("/admin/media", json={"kind": "image", "url": ext_url,
                                           "download": False})
        check(r.json().get("url") == ext_url if r.status_code in (200, 201) else False,
              "legacy add download=false tetap hotlink (kompatibel)",
              str(r.status_code))
        if legadd.get("id"):
            r = api.delete(f"/admin/media/{legadd['id']}")
            check(r.status_code == 200, "DELETE /admin/media/{id} legacy tetap jalan",
                  str(r.status_code))
        # berkas datar warisan (backend/media/*.png)
        flat = [p for p in MEDIA_ROOT.glob("*.png")][:3]
        if flat:
            for p in flat:
                rr = client.get(f"{BASE}/api/media/{p.name}")
                check(rr.status_code == 200, f"berkas datar warisan {p.name} -> 200",
                      str(rr.status_code))
        else:
            NOTES.append("tidak ada berkas datar warisan untuk diuji")
        r = api.post("/admin/media/maintenance/migrate")
        check(r.status_code == 200, "endpoint migrasi idempotent", str(r.json())[:120])

        # ---------- 15. LOKALISASI URL EKSTERNAL (anti broken image) ----------
        head("15. Lokalisasi gambar eksternal + penulisan ulang referensi")
        r = api.post("/admin/media", json={"kind": "image", "url": ext_url,
                                           "download": False})
        hot = r.json() if r.status_code in (200, 201) else {}
        check(hot.get("url") == ext_url, "aset hotlink dibuat untuk uji", str(r.status_code))
        # pasang hotlink ke produk + kategori supaya referensi bisa diuji
        r = api.get("/admin/products?limit=1")
        pl = r.json()
        plist2 = (pl.get("items") if isinstance(pl, dict) else pl) or []
        cat_id = None
        if plist2:
            pid2 = plist2[0]["id"]
            full2 = api.get(f"/admin/products/{pid2}").json()
            pay2 = {k: v for k, v in full2.items()
                    if k not in ("_id", "created_at", "updated_at", "rating", "review_count")}
            pay2["images"] = [ext_url]
            api.put(f"/admin/products/{pid2}", json=pay2)
        cats = api.get("/admin/categories").json() or []
        if cats:
            cat_id = cats[0]["id"]
            api.put(f"/admin/categories/{cat_id}", json={
                "name": cats[0]["name"], "slug": cats[0]["slug"],
                "desc": cats[0].get("desc", ""), "image": ext_url, "active": True,
            })
        st = api.get("/admin/media/stats").json()
        check(st.get("hotlinked", 0) >= 1, "statistik mendeteksi gambar hotlink",
              f"hotlinked={st.get('hotlinked')}")
        r = api.post("/admin/media/maintenance/localize")
        loc = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200 and loc.get("converted", 0) >= 1,
              "POST maintenance/localize mengunduh gambar eksternal",
              f"{r.status_code} converted={loc.get('converted')}")
        check(loc.get("refs_updated", 0) >= 1, "referensi produk/kategori diperbarui",
              f"refs={loc.get('refs_updated')}")
        if plist2:
            p_after = api.get(f"/admin/products/{plist2[0]['id']}").json()
            check(all(str(u).startswith("/api/media/") for u in (p_after.get("images") or [])),
                  "galeri produk kini menunjuk berkas LOKAL",
                  str(p_after.get("images"))[:100])
        if cat_id:
            cat_after = [c for c in (api.get("/admin/categories").json() or [])
                         if c["id"] == cat_id]
            img = (cat_after[0].get("image") if cat_after else "") or ""
            check(img.startswith("/api/media/"), "gambar kategori kini LOKAL", img[:80])
            rr = api.raw(img)
            check(rr.status_code == 200, "gambar kategori hasil lokalisasi tersaji 200",
                  str(rr.status_code))
        st2 = api.get("/admin/media/stats").json()
        check(st2.get("hotlinked", 0) == 0, "tidak ada lagi gambar hotlink",
              f"hotlinked={st2.get('hotlinked')}")
        r = api.post("/admin/media/maintenance/localize")
        check(r.status_code == 200 and r.json().get("converted", 0) == 0,
              "localize idempotent (jalan kedua: 0 konversi)", str(r.json().get("converted")))

        # ---------- bersih-bersih ----------
        head("Bersih-bersih fixture POC")
        r = api.get(f"/admin/media/assets?folder_id={f1['id']}&recursive=true&limit=200")
        for a in r.json().get("items", []):
            api.delete(f"/admin/media/assets/{a['id']}")
        r = api.delete(f"/admin/media/folders/{f1['id']}?cascade=true")
        ok("fixture folder POC dihapus", str(r.status_code))

    # ---------- ringkasan ----------
    print(f"\n{C}{'=' * 62}{X}")
    total = len(PASS) + len(FAIL)
    print(f"  HASIL: {G}{len(PASS)} PASS{X} / {R}{len(FAIL)} FAIL{X} dari {total} cek")
    for n in NOTES:
        print(f"  {Y}note:{X} {n}")
    if FAIL:
        print(f"\n{R}GAGAL:{X}")
        for name, det in FAIL:
            print(f"  - {name}: {det}")
    print(f"{C}{'=' * 62}{X}")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
