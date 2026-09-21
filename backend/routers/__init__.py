"""routers/ — lapisan I/O (THIN). Tiap file = satu domain/area.

Semua router menggunakan prefix '/api' (via server.py) agar lolos Kubernetes ingress.
Router TIDAK boleh berisi logika bisnis berat -> pindahkan ke services/.
"""
