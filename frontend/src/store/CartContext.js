import React, { createContext, useContext, useEffect, useMemo, useReducer, useRef } from 'react';
import { validateVoucher } from '../services/vouchers';
import { track } from '../services/analytics';

const CartContext = createContext(null);

const STORAGE_KEY = 'cp:cart:v1';

const load = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { items: [], voucher: null, note: '' };
    return JSON.parse(raw);
  } catch (e) {
    return { items: [], voucher: null, note: '' };
  }
};

const save = (state) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    /* ignore */
  }
};

const init = { items: [], voucher: null, note: '', isOpen: false, _hydrated: false };

function reducer(state, action) {
  switch (action.type) {
    case 'HYDRATE':
      return { ...state, ...action.payload, _hydrated: true };
    case 'OPEN':
      return { ...state, isOpen: true };
    case 'CLOSE':
      return { ...state, isOpen: false };
    case 'ADD': {
      const { product, volume, quantity } = action.payload;
      const vtype = volume.type || '';
      const sku = volume.sku || null;
      // Identitas baris: SKU (baru) → fallback (type::ml) untuk kompat.
      const key = sku ? `${product.id}::${sku}` : `${product.id}::${vtype}::${volume.ml}`;
      const existing = state.items.find((i) => i.key === key);
      let items;
      if (existing) {
        items = state.items.map((i) => (i.key === key ? { ...i, quantity: i.quantity + quantity } : i));
      } else {
        items = [
          ...state.items,
          {
            key,
            productId: product.id,
            slug: product.slug,
            name: product.name,
            brand: product.brand,
            category: product.category, // untuk evaluasi scope voucher (E2)
            image: product.images[0],
            concentration: product.concentration,
            variantType: vtype,          // label dimensi non-ukuran (composite)
            variantLabel: volume.label || '',   // label lengkap semua dimensi (display)
            options: volume.options || {},      // {DimName: value} snapshot (N-dimensi)
            sku,
            volumeMl: volume.ml,
            unitPrice: volume.price,
            stock: Number.isFinite(Number(volume.stock)) ? Number(volume.stock) : null, // snapshot stok utk cap qty (UX)
            quantity,
          },
        ];
      }
      return { ...state, items, isOpen: true };
    }
    case 'UPDATE_QTY': {
      const { key, quantity } = action.payload;
      const items = state.items
        .map((i) => (i.key === key ? { ...i, quantity: Math.max(0, quantity) } : i))
        .filter((i) => i.quantity > 0);
      return { ...state, items };
    }
    case 'REMOVE':
      return { ...state, items: state.items.filter((i) => i.key !== action.payload) };
    case 'CLEAR':
      return { ...state, items: [], voucher: null, note: '' };
    case 'APPLY_VOUCHER':
      // payload = hasil validate server {code,type,value,discount,label,min_spend} atau null
      return { ...state, voucher: action.payload };
    case 'SET_NOTE':
      return { ...state, note: action.payload };
    default:
      return state;
  }
}

export const CartProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, init);

  useEffect(() => {
    dispatch({ type: 'HYDRATE', payload: load() });
  }, []);

  // Persist HANYA setelah hydrate selesai — cegah race yang menimpa localStorage
  // dengan state awal kosong saat full reload (F5) di halaman keranjang/checkout.
  // Field di-destructure agar dep array eksplisit (bukan objek `state` utuh).
  const {
    _hydrated: cartHydrated, items: cartItems, voucher: cartVoucher, note: cartNote,
  } = state;
  useEffect(() => {
    if (!cartHydrated) return;
    save({ items: cartItems, voucher: cartVoucher, note: cartNote });
  }, [cartHydrated, cartItems, cartVoucher, cartNote]);

  const subtotal = useMemo(
    () => state.items.reduce((s, i) => s + i.unitPrice * i.quantity, 0),
    [state.items]
  );

  // Re-validasi voucher saat subtotal/isi keranjang berubah — diskon SELALU dari server (SSOT).
  // Konteks keranjang tanpa ongkir (shipping=0); free_shipping dihitung penuh di checkout.
  const lastRef = useRef({ code: null, subtotal: null });
  useEffect(() => {
    const code = state.voucher?.code;
    if (!code) {
      lastRef.current = { code: null, subtotal };
      return;
    }
    if (lastRef.current.code === code && lastRef.current.subtotal === subtotal) return;
    lastRef.current = { code, subtotal };
    let active = true;
    (async () => {
      try {
        const res = await validateVoucher({ code, subtotal, items: state.items });
        if (!active) return;
        dispatch({ type: 'APPLY_VOUCHER', payload: res.valid ? res : null });
      } catch (e) {
        /* jaringan gagal — pertahankan state voucher saat ini */
      }
    })();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subtotal, state.voucher?.code]);

  const value = useMemo(() => {
    const totalQty = state.items.reduce((s, i) => s + i.quantity, 0);
    // Diskon dari respons API (server), BUKAN dihitung ulang di klien (E2 display SSOT).
    const discount = Math.min(subtotal, Math.max(0, Number(state.voucher?.discount) || 0));
    return {
      ...state,
      subtotal,
      discount,
      totalQty,
      open: () => dispatch({ type: 'OPEN' }),
      close: () => dispatch({ type: 'CLOSE' }),
      addItem: (product, volume, quantity = 1) => {
        // Analytics first-party (E7): event add_to_cart, best-effort & PII-free.
        track('add_to_cart', { product_id: product?.id, meta: { type: volume?.type || '', ml: volume?.ml, qty: quantity } });
        dispatch({ type: 'ADD', payload: { product, volume, quantity } });
      },
      updateQty: (key, quantity) => dispatch({ type: 'UPDATE_QTY', payload: { key, quantity } }),
      removeItem: (key) => dispatch({ type: 'REMOVE', payload: key }),
      clear: () => dispatch({ type: 'CLEAR' }),
      applyVoucher: (v) => dispatch({ type: 'APPLY_VOUCHER', payload: v }),
      removeVoucher: () => dispatch({ type: 'APPLY_VOUCHER', payload: null }),
      setNote: (n) => dispatch({ type: 'SET_NOTE', payload: n }),
    };
  }, [state, subtotal]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

export const useCart = () => {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
};
