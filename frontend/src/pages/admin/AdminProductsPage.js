// pages/admin/AdminProductsPage.js — tabel produk + toolbar + AKSI MASSAL (BR-2).
import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Plus, Search, MoreHorizontal, Pencil, Archive, RotateCcw, ExternalLink, Download, Upload, FileSpreadsheet, FileText } from 'lucide-react';
import { listProducts, archiveProduct, restoreProduct, exportProducts, bulkProductStatus } from '../../services/admin';
import { formatIDR } from '../../lib/format';
import { PageHeader, TableSkeleton, EmptyState } from '../../components/admin/adminUi';
import { ProductsBulkBar } from '../../components/admin/products/ProductsBulkBar';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Checkbox } from '../../components/ui/checkbox';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem,
} from '../../components/ui/dropdown-menu';
import {
  AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle,
  AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '../../components/ui/alert-dialog';

const PAGE_SIZE = 50;

export default function AdminProductsPage() {
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('all');
  const [q, setQ] = useState('');
  // --- aksi massal ---
  const [selected, setSelected] = useState([]);   // id produk tercentang (lintas halaman)
  const [allFilter, setAllFilter] = useState(false); // cakupan = SELURUH hasil filter
  const [bulkBusy, setBulkBusy] = useState(false);

  const load = useCallback(async (pageArg) => {
    const p = typeof pageArg === 'number' ? pageArg : page;
    setLoading(true);
    try {
      const { items, total: t } = await listProducts({
        status: status === 'all' ? '' : status,
        q,
        limit: PAGE_SIZE,
        skip: p * PAGE_SIZE,
      });
      setRows(items || []);
      setTotal(t || 0);
    } catch (e) {
      toast.error('Gagal memuat produk.');
    } finally {
      setLoading(false);
    }
  }, [status, q, page]);

  // Ganti filter/pencarian -> selalu balik ke halaman pertama & bersihkan pilihan
  // (cakupan berubah, jadi seleksi lama tidak lagi bermakna).
  useEffect(() => { setPage(0); setSelected([]); setAllFilter(false); }, [status, q]);
  useEffect(() => { load(); }, [status, page]); // eslint-disable-line
  useEffect(() => {
    const t = setTimeout(() => load(0), 350);
    return () => clearTimeout(t);
  }, [q]); // eslint-disable-line

  const selectedSet = useMemo(() => new Set(selected), [selected]);
  const pageIds = useMemo(() => rows.map((r) => r.id), [rows]);
  const pageAllChecked = pageIds.length > 0 && pageIds.every((id) => selectedSet.has(id));

  const toggleRow = (id) => {
    setAllFilter(false);
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };
  const togglePage = () => {
    setAllFilter(false);
    setSelected((prev) => (pageAllChecked
      ? prev.filter((id) => !pageIds.includes(id))
      : Array.from(new Set([...prev, ...pageIds]))));
  };
  const clearSelection = () => { setSelected([]); setAllFilter(false); };

  const applyBulk = async (nextStatus) => {
    setBulkBusy(true);
    try {
      const res = allFilter
        ? await bulkProductStatus({
          status: nextStatus,
          filterStatus: status === 'all' ? 'all' : status,
          q,
          confirmCount: total,
        })
        : await bulkProductStatus({ status: nextStatus, ids: selected });
      toast.success(`${res.modified} produk ${nextStatus === 'active' ? 'diaktifkan' : 'diarsipkan'}.`);
      clearSelection();
      load();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      toast.error(detail || 'Gagal menjalankan aksi massal.');
      if (e?.response?.status === 409) load();
    } finally {
      setBulkBusy(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const from = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const to = Math.min(total, (page + 1) * PAGE_SIZE);

  const doArchive = async (id) => {
    try { await archiveProduct(id); toast.success('Produk diarsipkan.'); load(); }
    catch (e) { toast.error('Gagal mengarsipkan.'); }
  };
  const doRestore = async (id) => {
    try { await restoreProduct(id); toast.success('Produk dipulihkan.'); load(); }
    catch (e) { toast.error('Gagal memulihkan.'); }
  };

  const [exporting, setExporting] = useState('');
  const doExport = async (format) => {
    setExporting(format);
    try {
      await exportProducts(format);
      toast.success(`Ekspor ${format.toUpperCase()} dimulai — cek unduhan Anda.`);
    } catch (e) {
      toast.error('Gagal mengekspor produk.');
    } finally {
      setExporting('');
    }
  };

  return (
    <div>
      <PageHeader
        title="Produk"
        description="Kelola katalog parfum, varian, dan media."
        actions={(
          <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2" data-testid={T.ioExportMenu} disabled={!!exporting}>
                  <Download className="h-4 w-4" /> {exporting ? 'Mengekspor…' : 'Ekspor'}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => doExport('csv')} data-testid={T.ioExportCsv}>
                  <FileText className="h-4 w-4 mr-2" /> Ekspor CSV
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => doExport('xlsx')} data-testid={T.ioExportXlsx}>
                  <FileSpreadsheet className="h-4 w-4 mr-2" /> Ekspor Excel (.xlsx)
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button variant="outline" onClick={() => navigate('/admin/produk/impor')}
              className="gap-2" data-testid={T.ioImportButton}>
              <Upload className="h-4 w-4" /> Impor
            </Button>
            <Button onClick={() => navigate('/admin/produk/baru')} data-testid={T.productsAdd} className="gap-2">
              <Plus className="h-4 w-4" /> Tambah Produk
            </Button>
          </>
        )}
      />

      <Card className="border-border/70">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari nama / merek / slug…"
                className="pl-9" data-testid={T.productsSearch} />
            </div>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-full sm:w-48" data-testid={T.productsStatusFilter}>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Status</SelectItem>
                <SelectItem value="active">Aktif</SelectItem>
                <SelectItem value="archived">Diarsipkan</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <ProductsBulkBar
            selectedCount={selected.length}
            total={total}
            allFilter={allFilter}
            pageCount={pageIds.length}
            busy={bulkBusy}
            onSelectAllFilter={() => setAllFilter(true)}
            onClear={clearSelection}
            onApply={applyBulk}
          />

          {loading ? <TableSkeleton rows={6} cols={5} /> : (
            rows.length === 0 ? (
              <EmptyState title="Belum ada produk" hint="Tambahkan produk pertama Anda."
                action={<Button onClick={() => navigate('/admin/produk/baru')} className="gap-2"><Plus className="h-4 w-4" /> Tambah Produk</Button>} />
            ) : (
              <div className="overflow-x-auto">
                <Table data-testid={T.productsTable}>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">
                        <Checkbox
                          checked={pageAllChecked}
                          onCheckedChange={togglePage}
                          aria-label="Pilih semua produk di halaman ini"
                          data-testid={T.productsSelectAll}
                        />
                      </TableHead>
                      <TableHead>Produk</TableHead>
                      <TableHead>Kategori</TableHead>
                      <TableHead className="text-right">Harga</TableHead>
                      <TableHead className="text-center">Varian</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-10" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((p) => (
                      <TableRow
                        key={p.id}
                        data-testid={T.productsRow}
                        className={selectedSet.has(p.id) || allFilter ? 'bg-muted/40' : ''}
                      >
                        <TableCell>
                          <Checkbox
                            checked={allFilter || selectedSet.has(p.id)}
                            onCheckedChange={() => toggleRow(p.id)}
                            aria-label={`Pilih ${p.name}`}
                            data-testid={T.productsRowCheckbox}
                          />
                        </TableCell>
                        <TableCell>
                          <div className="font-medium truncate max-w-[240px]">{p.name}</div>
                          <div className="text-[11px] text-muted-foreground font-[\'Azeret_Mono\',monospace]">{p.slug}</div>
                        </TableCell>
                        <TableCell className="capitalize text-sm text-muted-foreground">{p.category}</TableCell>
                        <TableCell className="text-right font-[\'Azeret_Mono\',monospace] text-sm">{formatIDR(p.price || 0)}</TableCell>
                        <TableCell className="text-center text-sm">{(p.volumes || []).length}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={p.status === 'active'
                            ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                            : 'bg-zinc-100 text-zinc-600 border-zinc-200'}>
                            {p.status === 'active' ? 'Aktif' : 'Diarsipkan'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" aria-label="Aksi" data-testid="admin-products-row-action">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => navigate(`/admin/produk/${p.id}`)}>
                                <Pencil className="h-4 w-4 mr-2" /> Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => window.open(`/parfum/${p.slug}`, '_blank')}>
                                <ExternalLink className="h-4 w-4 mr-2" /> Lihat di toko
                              </DropdownMenuItem>
                              {p.status === 'active' ? (
                                <AlertDialog>
                                  <AlertDialogTrigger asChild>
                                    <DropdownMenuItem onSelect={(e) => e.preventDefault()} className="text-rose-600">
                                      <Archive className="h-4 w-4 mr-2" /> Arsipkan
                                    </DropdownMenuItem>
                                  </AlertDialogTrigger>
                                  <AlertDialogContent>
                                    <AlertDialogHeader>
                                      <AlertDialogTitle>Arsipkan produk?</AlertDialogTitle>
                                      <AlertDialogDescription>
                                        Produk disembunyikan dari storefront namun tetap tersimpan (aman untuk pesanan lama).
                                      </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                      <AlertDialogCancel>Batal</AlertDialogCancel>
                                      <AlertDialogAction onClick={() => doArchive(p.id)}>Arsipkan</AlertDialogAction>
                                    </AlertDialogFooter>
                                  </AlertDialogContent>
                                </AlertDialog>
                              ) : (
                                <DropdownMenuItem onClick={() => doRestore(p.id)}>
                                  <RotateCcw className="h-4 w-4 mr-2" /> Pulihkan
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )
          )}

          {/* Paginasi — WAJIB: katalog bisa berisi ribuan produk (impor massal). */}
          {!loading && total > 0 ? (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border/70 pt-3">
              <div className="text-xs text-muted-foreground" data-testid={T.productsPageInfo}>
                Menampilkan <span className="font-medium text-foreground">{from}–{to}</span> dari{' '}
                <span className="font-medium text-foreground">{total}</span> produk
                {totalPages > 1 ? ` · halaman ${page + 1}/${totalPages}` : ''}
              </div>
              {totalPages > 1 ? (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 0}
                    onClick={() => setPage((v) => Math.max(0, v - 1))}
                    data-testid={T.productsPrevPage}
                  >
                    Sebelumnya
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page + 1 >= totalPages}
                    onClick={() => setPage((v) => v + 1)}
                    data-testid={T.productsNextPage}
                  >
                    Berikutnya
                  </Button>
                </div>
              ) : null}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
