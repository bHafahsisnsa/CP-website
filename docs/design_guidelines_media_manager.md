{
  "design_system_name": "Collector Parfum Admin — Media Manager Extension",
  "visual_personality": {
    "brand_attributes": [
      "premium (brass/champagne accent)",
      "trustworthy & forgiving (clear states, undo-friendly)",
      "dense-but-breathable admin (2–3x spacing, strong hierarchy)",
      "file-manager familiar (tree → grid/list → inspector)"
    ],
    "do_not_change": [
      "Keep existing LIGHT admin theme and semantic tokens (bg-background, bg-card, text-foreground, border-border, bg-muted/*).",
      "Keep brass accent ACCENT #B89B6A and ACCENT_SOFT rgba(184,155,106,0.12).",
      "Keep typography: DM Serif Display for headings, Manrope for body, Azeret Mono for mono.",
      "Do not introduce a new palette. Extend only with derived tints using existing tokens.",
      "All UI copy must be Bahasa Indonesia.",
      "All interactive + key informational elements MUST have data-testid (kebab-case, role-based)."
    ]
  },
  "design_tokens": {
    "source_of_truth": [
      "/app/frontend/src/index.css (CSS variables + cp-* tokens)",
      "/app/frontend/src/components/admin/adminUi.js (ACCENT, ACCENT_SOFT)"
    ],
    "colors": {
      "semantic_usage": {
        "page_bg": "bg-background",
        "card_bg": "bg-card",
        "muted_bg": "bg-muted/40 (panels) and bg-muted/60 (hover/selected rails)",
        "text_primary": "text-foreground",
        "text_secondary": "text-muted-foreground",
        "borders": "border-border and border-border/70",
        "focus_ring": "ring-[hsl(var(--ring))] + :focus-visible outline already set in index.css",
        "accent": "use ACCENT (#B89B6A) for active/selected emphasis only",
        "accent_soft": "use ACCENT_SOFT for selection wash / drop targets"
      },
      "state_colors": {
        "success": "bg-emerald-100 text-emerald-800 border-emerald-200",
        "warning": "bg-amber-100 text-amber-800 border-amber-200",
        "info": "bg-blue-100 text-blue-800 border-blue-200",
        "danger": "bg-rose-100 text-rose-800 border-rose-200",
        "destructive": "bg-destructive text-destructive-foreground"
      },
      "special_surfaces": {
        "checkerboard_for_transparency": "Use CSS background-size 12px 12px with two-tone using border-border/40 and bg-muted/60",
        "dropzone_overlay": "bg-background/70 backdrop-blur-[2px] + border-2 border-dashed"
      }
    },
    "typography": {
      "fonts": {
        "display": "DM Serif Display",
        "body": "Manrope",
        "mono": "Azeret Mono"
      },
      "scale": {
        "h1": "text-2xl sm:text-3xl (admin PageHeader already)",
        "h2": "text-base sm:text-lg font-medium",
        "body": "text-sm (admin default), long text max-w-prose",
        "meta": "text-xs text-muted-foreground",
        "eyebrow": "text-[10px] uppercase tracking-[0.16em] text-muted-foreground"
      }
    },
    "radius_shadow": {
      "radius": {
        "cards": "rounded-2xl",
        "tiles": "rounded-xl",
        "inputs_buttons": "rounded-md to rounded-lg",
        "badges": "rounded-full"
      },
      "shadows": {
        "rest": "shadow-sm",
        "hover": "shadow-md (only on tiles/cards that are clickable)",
        "drawer": "shadow-xl"
      }
    },
    "spacing": {
      "page_gutter": "px-4 sm:px-6",
      "rail_gap": "gap-4",
      "toolbar_height": "min-h-12",
      "tile_gap": "gap-3 sm:gap-4",
      "list_row_height": "h-12 (dense) / h-14 (comfortable)"
    }
  },
  "layout_specs": {
    "admin_media_page": {
      "route": "/admin/media",
      "overall_pattern": "3-column master-detail: Folder rail (left) + Asset canvas (center) + Details inspector (right)",
      "grid": {
        "desktop": {
          "container": "w-full",
          "columns": "grid grid-cols-12 gap-4",
          "left_rail": "col-span-3 xl:col-span-2 min-w-[260px] max-w-[320px]",
          "center": "col-span-9 xl:col-span-7",
          "right_inspector": "hidden xl:block xl:col-span-3 min-w-[320px] max-w-[420px]"
        },
        "tablet": {
          "left_rail": "col-span-4 min-w-[240px]",
          "center": "col-span-8",
          "right_inspector": "use Sheet (right) instead of persistent panel"
        },
        "mobile": {
          "left_rail": "collapses into Sheet (left) opened by 'Folder' button",
          "center": "full width",
          "right_inspector": "Sheet (bottom on very small screens, right on >=sm)"
        }
      },
      "sticky_regions": {
        "toolbar": "Sticky within center column: top-0 z-10 bg-background/80 backdrop-blur border-b",
        "bulk_action_bar": "Sticky bottom-4 within center column (or fixed bottom on mobile)"
      }
    },
    "details_panel_behavior": {
      "desktop_xl": "Persistent right inspector panel (Card) with ScrollArea.",
      "below_xl": "Use <Sheet side=\"right\"> for inspector; open when an asset is focused.",
      "mobile_small": "If preview is tall, use <Drawer> (bottom sheet) for inspector to avoid cramped width."
    }
  },
  "component_inventory": {
    "shadcn_primitives": {
      "paths": [
        "frontend/src/components/ui/button.jsx",
        "frontend/src/components/ui/input.jsx",
        "frontend/src/components/ui/select.jsx",
        "frontend/src/components/ui/dialog.jsx",
        "frontend/src/components/ui/sheet.jsx",
        "frontend/src/components/ui/drawer.jsx",
        "frontend/src/components/ui/tabs.jsx",
        "frontend/src/components/ui/scroll-area.jsx",
        "frontend/src/components/ui/progress.jsx",
        "frontend/src/components/ui/checkbox.jsx",
        "frontend/src/components/ui/dropdown-menu.jsx",
        "frontend/src/components/ui/popover.jsx",
        "frontend/src/components/ui/tooltip.jsx",
        "frontend/src/components/ui/breadcrumb.jsx",
        "frontend/src/components/ui/card.jsx",
        "frontend/src/components/ui/badge.jsx",
        "frontend/src/components/ui/table.jsx",
        "frontend/src/components/ui/skeleton.jsx",
        "frontend/src/components/ui/pagination.jsx",
        "frontend/src/components/ui/separator.jsx",
        "frontend/src/components/ui/collapsible.jsx",
        "frontend/src/components/ui/context-menu.jsx",
        "frontend/src/components/ui/command.jsx",
        "frontend/src/components/ui/sonner.jsx"
      ]
    },
    "admin_atoms_to_reuse": {
      "PageHeader": {
        "path": "frontend/src/components/admin/adminUi.js",
        "props": "{ title, description, actions, testId }"
      },
      "EmptyState": {
        "path": "frontend/src/components/admin/adminUi.js",
        "props": "{ title, hint, action }"
      },
      "MetricCard": {
        "path": "frontend/src/components/admin/adminUi.js",
        "props": "{ label, value, sub, testId, accent }"
      }
    },
    "new_components_to_build_js": {
      "AdminMediaPage": {
        "type": "page",
        "responsibilities": [
          "folder tree rail",
          "toolbar + breadcrumb",
          "asset grid/list",
          "upload overlay + queue",
          "bulk actions",
          "details inspector"
        ]
      },
      "FolderTree": {
        "type": "component",
        "props": {
          "folders": "array",
          "activeFolderId": "string",
          "onSelectFolder": "fn(folderId)",
          "onCreateFolder": "fn(parentId)",
          "onRenameFolder": "fn(folderId, name)",
          "onDeleteFolder": "fn(folderId)",
          "onMoveFolder": "fn(dragId, targetId)"
        },
        "notes": "Use Collapsible for nested nodes; provide non-drag fallback via dropdown menu 'Pindahkan ke…'."
      },
      "AssetToolbar": {
        "type": "component",
        "props": {
          "query": "string",
          "onQueryChange": "fn",
          "typeFilter": "string",
          "sort": "string",
          "view": "grid|list",
          "selectedCount": "number",
          "onUploadClick": "fn",
          "onNewFolderClick": "fn",
          "onToggleView": "fn"
        }
      },
      "AssetGrid": {
        "type": "component",
        "props": {
          "items": "array",
          "selectedIds": "Set",
          "focusedId": "string",
          "onToggleSelect": "fn(id)",
          "onFocus": "fn(id)",
          "onOpen": "fn(id)",
          "view": "grid",
          "isLoading": "bool"
        }
      },
      "AssetList": {
        "type": "component",
        "props": {
          "items": "array",
          "selectedIds": "Set",
          "focusedId": "string",
          "onToggleSelect": "fn(id)",
          "onFocus": "fn(id)",
          "onOpen": "fn(id)",
          "isLoading": "bool"
        }
      },
      "AssetTile": {
        "type": "component",
        "props": {
          "item": "{ id, name, mime, size, width, height, thumbUrl, updatedAt }",
          "selected": "bool",
          "focused": "bool",
          "onSelect": "fn",
          "onOpenDetails": "fn"
        }
      },
      "AssetDetailsPanel": {
        "type": "component",
        "props": {
          "item": "asset",
          "onRename": "fn",
          "onUpdateAlt": "fn",
          "onMove": "fn(folderId)",
          "onReplace": "fn(file)",
          "onDelete": "fn",
          "onCopyUrl": "fn"
        }
      },
      "UploadQueuePanel": {
        "type": "component",
        "props": {
          "queue": "array of { id, fileName, progress, status, error }",
          "onCancel": "fn(id)",
          "onRetry": "fn(id)",
          "onClearDone": "fn"
        }
      },
      "MediaPickerDialog": {
        "type": "component",
        "props": {
          "open": "bool",
          "onOpenChange": "fn",
          "mode": "single|multi",
          "value": "asset or assets",
          "onConfirm": "fn(selectedAssets)",
          "allowedTypes": "array",
          "title": "string (default: 'Pilih Media')"
        }
      },
      "MediaField": {
        "type": "component",
        "props": {
          "label": "string",
          "value": "asset|null",
          "onChange": "fn(asset|null)",
          "mode": "single",
          "hint": "string"
        }
      },
      "SmartImage": {
        "type": "component",
        "props": {
          "src": "string",
          "alt": "string",
          "className": "string",
          "fallback": "'placeholder'|'initials'",
          "onError": "fn"
        },
        "behavior": "Show Skeleton while loading; on error show branded placeholder + 'Coba muat ulang' button; never show broken-image icon."
      }
    }
  },
  "ui_specs": {
    "folder_tree": {
      "rail_container_classes": "rounded-2xl border border-border/70 bg-card",
      "rail_header": {
        "title": "Folder",
        "classes": "px-4 py-3 border-b border-border/70 flex items-center justify-between",
        "actions": [
          "Folder Baru (Button size=sm variant=secondary)",
          "Menu (DropdownMenu)"
        ]
      },
      "row_spec": {
        "height": "h-9",
        "indent": "pl-[calc(12px+depth*14px)] (implement via inline style or class map)",
        "chevron": "lucide ChevronRight; rotates 90deg when open",
        "icon": "Folder / FolderOpen",
        "count_pill": "Badge variant=secondary className='ml-auto text-[11px] px-2 py-0.5 rounded-full'",
        "active_state": "bg-[ACCENT_SOFT] text-foreground border border-[ACCENT]/30",
        "hover_state": "hover:bg-muted/60",
        "drop_target_state": "ring-2 ring-[ACCENT]/40 bg-[ACCENT_SOFT]",
        "context_menu": [
          "Buat folder di sini",
          "Ubah nama",
          "Hapus",
          "Pindahkan ke… (fallback non-drag)"
        ]
      },
      "empty_state": {
        "title": "Belum ada folder",
        "hint": "Buat folder untuk merapikan media. Anda bisa membuat folder bertingkat tanpa batas.",
        "action": "Button: 'Folder Baru'"
      }
    },
    "breadcrumb_and_toolbar": {
      "breadcrumb": {
        "component": "shadcn Breadcrumb",
        "classes": "text-xs text-muted-foreground",
        "items": "Beranda / Media / (folder path)"
      },
      "toolbar_container_classes": "sticky top-0 z-10 bg-background/80 backdrop-blur border-b border-border/70",
      "toolbar_inner_classes": "flex flex-col gap-3 px-0 py-3",
      "row_1_actions": [
        {
          "label": "Upload",
          "component": "Button",
          "variant": "default",
          "classes": "rounded-lg",
          "icon": "Upload",
          "testid": "admin-media-upload-btn"
        },
        {
          "label": "Folder Baru",
          "component": "Button",
          "variant": "secondary",
          "icon": "FolderPlus",
          "testid": "admin-media-new-folder-btn"
        }
      ],
      "row_2_controls": [
        {
          "control": "Search",
          "component": "Input",
          "placeholder": "Cari nama file…",
          "classes": "h-10",
          "testid": "admin-media-search-input"
        },
        {
          "control": "Type filter",
          "component": "Select",
          "options": "Semua, Gambar, Video, Dokumen, SVG, GIF",
          "testid": "admin-media-type-filter"
        },
        {
          "control": "Sort",
          "component": "Select",
          "options": "Terbaru, Nama A–Z, Ukuran terbesar",
          "testid": "admin-media-sort-select"
        },
        {
          "control": "View toggle",
          "component": "ToggleGroup or two Buttons",
          "options": "Grid, List",
          "testid": "admin-media-view-toggle"
        }
      ]
    },
    "asset_grid": {
      "grid_container": "grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4",
      "tile": {
        "aspect_ratio": "aspect-[4/3] for images; keep consistent to reduce layout shift",
        "tile_classes": "group relative rounded-2xl border border-border/70 bg-card shadow-sm overflow-hidden",
        "hover": "hover:shadow-md hover:border-border",
        "focus": "focus-within:ring-2 focus-within:ring-[hsl(var(--ring))]",
        "selection": "ring-2 ring-[ACCENT]/45 bg-[ACCENT_SOFT]",
        "thumbnail": {
          "wrapper": "relative w-full aspect-[4/3] bg-muted/40",
          "checkerboard": "apply only when mime indicates transparency (png/webp with alpha, svg) or unknown",
          "img": "object-cover w-full h-full",
          "lazy": "loading='lazy' decoding='async'"
        },
        "top_left_badges": [
          "SVG badge",
          "GIF badge",
          "HEIC badge",
          "AVIF badge"
        ],
        "top_right_actions": {
          "reveal": "opacity-0 group-hover:opacity-100 transition-opacity duration-150",
          "buttons": [
            "Checkbox select",
            "More menu (DropdownMenu)"
          ]
        },
        "meta_area": {
          "classes": "p-3",
          "line_1": "filename (truncate, font-medium text-sm)",
          "line_2": "size + updatedAt (text-xs text-muted-foreground)",
          "line_3_optional": "dimensions (mono text-[11px])"
        }
      }
    },
    "asset_list": {
      "table": {
        "component": "shadcn Table",
        "header": "Nama | Tipe | Ukuran | Diubah | Aksi",
        "row_classes": "hover:bg-muted/40",
        "row_height": "h-12",
        "selection": "bg-[ACCENT_SOFT]",
        "leading": "Checkbox + tiny thumb (w-10 h-10 rounded-lg)"
      },
      "empty_state": {
        "title": "Tidak ada media",
        "hint": "Upload file atau tambahkan dari URL untuk mulai mengisi pustaka media.",
        "action": "Button: 'Upload'"
      }
    },
    "drag_drop_dropzone": {
      "overlay": {
        "when": "dragenter/dragover on center canvas",
        "classes": "fixed inset-0 z-50 bg-background/70 backdrop-blur-[2px]",
        "panel": "mx-auto mt-24 max-w-2xl rounded-2xl border-2 border-dashed border-[ACCENT]/40 bg-card shadow-xl p-8 text-center",
        "copy": {
          "title": "Lepaskan untuk upload",
          "hint": "Maks 15MB per file. Format: JPG, PNG, WebP, GIF, SVG, AVIF, HEIC."
        },
        "fallback": "Always keep a visible 'Pilih File' button for non-drag users."
      }
    },
    "upload_queue": {
      "placement": "Right side under inspector on xl; otherwise collapsible bottom tray in center column",
      "container_classes": "rounded-2xl border border-border/70 bg-card",
      "header": "Upload (n) — Button 'Bersihkan selesai'",
      "row": {
        "layout": "filename + status badge + Progress bar + actions",
        "progress": "shadcn Progress className='h-2'",
        "status_badges": {
          "uploading": "Badge variant=secondary 'Mengunggah'",
          "done": "Badge className='bg-emerald-100 text-emerald-800 border-emerald-200'",
          "error": "Badge className='bg-rose-100 text-rose-800 border-rose-200'"
        },
        "actions": "Icon buttons: Batalkan, Coba lagi"
      },
      "errors": {
        "file_too_large": "Terlalu besar (maks 15MB)",
        "unsupported": "Format tidak didukung",
        "network": "Gagal upload. Periksa koneksi lalu coba lagi."
      }
    },
    "details_inspector": {
      "container": "rounded-2xl border border-border/70 bg-card shadow-sm",
      "sections": [
        "Preview (AspectRatio 4/3)",
        "Nama file + tombol Copy URL",
        "Info: tipe, ukuran, dimensi, dibuat/diubah",
        "Form: Ubah nama, Alt text",
        "Move: pilih folder (Popover + Command search)",
        "Replace file",
        "Danger zone: Hapus"
      ],
      "copy_url": "Use Button variant=secondary size=sm; toast 'Tautan disalin'.",
      "danger_zone": "Use AlertDialog confirm with clear copy; destructive button only inside dialog."
    },
    "bulk_action_bar": {
      "appearance": "Shows when selectedIds.size > 0",
      "classes": "sticky bottom-4 rounded-2xl border border-border/70 bg-card shadow-lg px-4 py-3 flex items-center justify-between",
      "left": "'3 dipilih' + 'Pilih semua hasil' link",
      "right_actions": [
        "Pindahkan ke…",
        "Hapus",
        "Batal"
      ]
    },
    "storage_stats_strip": {
      "placement": "Below PageHeader, above toolbar",
      "layout": "4 compact MetricCards in a 2x2 on mobile, 4-in-row on lg",
      "metrics": [
        "Jumlah file",
        "Total ukuran",
        "Jumlah folder",
        "Batas upload (15MB/file)"
      ]
    }
  },
  "media_picker_dialog_spec": {
    "component": "MediaPickerDialog",
    "dialog": {
      "component": "shadcn Dialog",
      "size": "w-[min(1100px,calc(100vw-2rem))] max-h-[85vh]",
      "layout": "Tabs on top; inside: left folder rail (optional) + grid/list + right selection tray",
      "tabs": [
        "Pustaka",
        "Upload",
        "Dari URL"
      ]
    },
    "pustaka_tab": {
      "layout": {
        "left": "Folder mini-tree (collapsible) width 240px (hidden on mobile -> Sheet)",
        "center": "Grid/list with search/filter/sort",
        "right": "Selection tray (only when multi or when single has selection)"
      },
      "selection_tray": {
        "multi": "Shows thumbnails in a horizontal ScrollArea + count + 'Hapus semua'",
        "single": "Shows one selected preview + filename",
        "confirm_button": "Primary: 'Pilih (n)' for multi, 'Pilih' for single",
        "confirm_testid": "admin-media-picker-confirm"
      }
    },
    "upload_tab": {
      "dropzone": "Same dropzone component; show queue inline",
      "copy": "Seret & lepas file di sini, atau klik untuk memilih file."
    },
    "from_url_tab": {
      "fields": [
        "Input URL",
        "Optional: Nama file",
        "Optional: Alt text"
      ],
      "primary_action": "Button: 'Unduh & Simpan'",
      "notes": "Downloads file to local storage on VPS; validate size/type; show progress + errors."
    },
    "footer": {
      "left": "Hint text: 'Maks 15MB/file'",
      "right": "Secondary: Batal, Primary: Pilih"
    }
  },
  "product_editor_media_tab_spec": {
    "section_title": "Media Produk",
    "gallery": {
      "grid": "grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3",
      "tile": {
        "aspect": "aspect-square",
        "classes": "relative rounded-xl border border-border/70 bg-card overflow-hidden",
        "primary_badge": "Badge className='absolute left-2 top-2 bg-[ACCENT_SOFT] text-foreground border border-[ACCENT]/30' text='Utama'",
        "actions": "Hover reveal: Set Utama, Hapus, Drag handle",
        "reorder": "Use drag handle icon; also provide non-drag fallback: 'Urutkan' dropdown with Move left/right"
      }
    },
    "add_paths": {
      "buttons": [
        "Pilih dari Media Manager (opens MediaPickerDialog in multi mode)",
        "Upload (opens Upload tab)",
        "Tambah dari URL (inline input + button)"
      ],
      "url_field": {
        "placeholder": "Tempel URL gambar…",
        "button": "Unduh & Tambahkan"
      }
    }
  },
  "smart_image_states": {
    "loading": "Skeleton with same aspect ratio; avoid layout shift",
    "loaded": "Fade in opacity transition-opacity duration-150",
    "error_missing": {
      "ui": "Placeholder card with icon ImageOff + text 'File tidak ditemukan' + button 'Coba muat ulang'",
      "copy": "Jika file sudah dihapus atau dipindahkan, pilih media lain.",
      "testids": {
        "placeholder": "smart-image-missing-placeholder",
        "retry": "smart-image-retry-button"
      }
    }
  },
  "microinteractions_motion": {
    "principles": [
      "Subtle, fast, and purposeful (150–220ms).",
      "Prefer opacity/color/shadow transitions; avoid transform-heavy animations on dense grids.",
      "Respect prefers-reduced-motion (disable non-essential animations)."
    ],
    "recipes": {
      "tile_hover": "transition-shadow duration-150 ease-out",
      "icon_button_hover": "transition-colors duration-150",
      "drawer_open": "Use shadcn Sheet default; keep content stable",
      "drop_target_pulse": "Optional: animate ring opacity with cp-pulse-soft only on drop overlay (not everywhere)"
    }
  },
  "accessibility": {
    "keyboard": [
      "Grid: arrow keys optional; minimum: Tab reaches each tile and its checkbox/menu.",
      "Enter opens details; Space toggles selection.",
      "Folder tree: arrow/enter to expand/select; ensure chevron button is focusable."
    ],
    "aria": [
      "Icon-only buttons must have aria-label.",
      "Images must have alt (use stored alt text; fallback to filename).",
      "Drag & drop must have non-drag alternatives for move and upload."
    ],
    "contrast": "Use semantic tokens; avoid transparent text on unknown backgrounds."
  },
  "performance_guidance": {
    "thumbnail_sizes": {
      "grid": "Use backend 400px WebP thumbs",
      "details": "Use 1000px medium",
      "lazy_loading": "Always loading='lazy' for grid; prefetch medium only when focused"
    },
    "pagination": {
      "default_page_size": 40,
      "controls": "Use shadcn Pagination; show 'Menampilkan 1–40 dari 312'"
    },
    "virtualization": "If > 500 items per folder, consider react-window later; keep DOM light by paginating first."
  },
  "copy_deck_id": {
    "page": {
      "title": "Media",
      "description": "Kelola gambar dan file untuk produk, konten, kategori, lokasi toko, dan pengaturan pembayaran."
    },
    "buttons": {
      "upload": "Upload",
      "new_folder": "Folder Baru",
      "from_url": "Dari URL",
      "download_save": "Unduh & Simpan",
      "choose": "Pilih",
      "choose_n": "Pilih ({n})",
      "cancel": "Batal",
      "delete": "Hapus",
      "move": "Pindahkan",
      "rename": "Ubah nama",
      "replace": "Ganti file",
      "copy_url": "Salin URL",
      "select_all": "Pilih semua",
      "clear_selection": "Batal pilih"
    },
    "empty_states": {
      "no_media": {
        "title": "Belum ada media",
        "hint": "Upload file pertama Anda atau tambahkan dari URL."
      },
      "no_results": {
        "title": "Tidak ada hasil",
        "hint": "Coba kata kunci lain atau ubah filter."
      },
      "empty_folder": {
        "title": "Folder ini kosong",
        "hint": "Seret file ke sini atau klik Upload."
      }
    },
    "confirmations": {
      "delete_asset_title": "Hapus file ini?",
      "delete_asset_desc": "File akan dihapus dari penyimpanan lokal dan tidak bisa dipulihkan.",
      "delete_folder_title": "Hapus folder ini?",
      "delete_folder_desc": "Folder dan seluruh isinya akan dihapus.",
      "bulk_delete_title": "Hapus {n} file?",
      "bulk_delete_desc": "Tindakan ini tidak bisa dibatalkan."
    },
    "errors": {
      "broken_image": "Gagal memuat gambar.",
      "upload_failed": "Upload gagal. Periksa koneksi lalu coba lagi.",
      "file_too_large": "Ukuran file melebihi 15MB.",
      "unsupported_format": "Format file tidak didukung.",
      "url_download_failed": "Gagal mengunduh dari URL. Pastikan tautan dapat diakses."
    },
    "toasts": {
      "copied": "Tautan disalin.",
      "uploaded": "Upload selesai.",
      "moved": "File dipindahkan.",
      "deleted": "File dihapus.",
      "renamed": "Nama diperbarui."
    }
  },
  "testid_plan": {
    "file_to_extend": "/app/frontend/src/constants/testIds/admin.js",
    "new_keys_to_add": {
      "mediaPage": "admin-media-page",
      "mediaFolderRail": "admin-media-folder-rail",
      "mediaFolderRow": "admin-media-folder-row",
      "mediaBreadcrumb": "admin-media-breadcrumb",
      "mediaToolbar": "admin-media-toolbar",
      "mediaUploadBtn": "admin-media-upload-btn",
      "mediaNewFolderBtn": "admin-media-new-folder-btn",
      "mediaSearchInput": "admin-media-search-input",
      "mediaTypeFilter": "admin-media-type-filter",
      "mediaSortSelect": "admin-media-sort-select",
      "mediaViewToggle": "admin-media-view-toggle",
      "mediaGrid": "admin-media-grid",
      "mediaList": "admin-media-list",
      "mediaTile": "admin-media-tile",
      "mediaTileCheckbox": "admin-media-tile-checkbox",
      "mediaBulkBar": "admin-media-bulk-bar",
      "mediaBulkMove": "admin-media-bulk-move",
      "mediaBulkDelete": "admin-media-bulk-delete",
      "mediaDetailsPanel": "admin-media-details-panel",
      "mediaDetailsRename": "admin-media-details-rename",
      "mediaDetailsAlt": "admin-media-details-alt",
      "mediaDetailsMove": "admin-media-details-move",
      "mediaDetailsDelete": "admin-media-details-delete",
      "mediaUploadQueue": "admin-media-upload-queue",
      "mediaUploadQueueRow": "admin-media-upload-queue-row",
      "mediaPickerDialog": "admin-media-picker-dialog",
      "mediaPickerConfirm": "admin-media-picker-confirm",
      "mediaField": "admin-media-field"
    }
  },
  "tailwind_class_recipes": {
    "icon_button": "h-9 w-9 rounded-lg border border-border/70 bg-card hover:bg-muted/60 transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]",
    "primary_button": "rounded-lg",
    "secondary_button": "rounded-lg",
    "chip": "inline-flex items-center rounded-full border border-border/70 bg-muted/40 px-2.5 py-1 text-xs text-foreground",
    "muted_panel": "rounded-2xl border border-border/70 bg-muted/40",
    "card": "rounded-2xl border border-border/70 bg-card shadow-sm",
    "danger_button": "bg-destructive text-destructive-foreground hover:bg-destructive/90"
  },
  "image_urls": {
    "note": "Admin media manager uses user-uploaded assets; no stock imagery required. Use placeholders only.",
    "placeholders": [
      {
        "category": "smart-image-fallback",
        "description": "Inline SVG placeholder (no external URL) with subtle border + icon",
        "image_url": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='480'><rect width='100%25' height='100%25' fill='%23f7f3ea'/><rect x='24' y='24' width='592' height='432' rx='24' fill='%23fffcf6' stroke='%23d6c3a3' stroke-width='2'/><path d='M220 250h200' stroke='%23141414' stroke-opacity='0.35' stroke-width='10' stroke-linecap='round'/><circle cx='260' cy='200' r='22' fill='%23141414' fill-opacity='0.18'/><path d='M240 320l70-80 60 70 40-45 90 105H240z' fill='%23141414' fill-opacity='0.12'/></svg>"
      }
    ]
  },
  "libraries": {
    "recommended": [
      {
        "name": "framer-motion",
        "status": "already referenced in index.css comments",
        "use_for": "Optional subtle entrance for dialogs/sheets only; avoid animating every tile"
      }
    ],
    "drag_drop": {
      "note": "If implementing complex drag between folders/assets, consider @dnd-kit/core later. But MUST provide non-drag fallback menus for move actions."
    }
  },
  "instructions_to_main_agent": [
    "Do NOT change global palette; use existing semantic tokens + ACCENT/ACCENT_SOFT only.",
    "Implement AdminMediaPage with 3-column layout; right inspector persistent only on xl; otherwise Sheet/Drawer.",
    "Use shadcn components from /frontend/src/components/ui (JSX). No raw HTML dropdowns/calendars/toasts.",
    "Every interactive element and key info must include data-testid; extend adminTestIds with the keys listed.",
    "Drag & drop: implement, but always include fallback actions (Move menu, Upload button).",
    "SmartImage must never show broken-image icon; show skeleton + fallback placeholder + retry.",
    "Keep animations subtle (150–220ms), no transition: all.",
    "Copy must be Bahasa Indonesia exactly as provided; keep confirmations explicit and undo-friendly where possible (toast with 'Urungkan' if feasible)."
  ],
  "appendix_general_ui_ux_design_guidelines": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
