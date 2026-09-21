// store/SettingsContext.js — SSOT setelan toko publik (GET /api/settings) untuk storefront.
// Satu kali fetch, dipakai bersama (footer, chat, label merek) supaya tidak ada request ganda.
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { fetchSettings } from '../services/config';

const SettingsContext = createContext({ settings: null, ready: false });

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let alive = true;
    fetchSettings()
      .then((d) => { if (alive) setSettings(d || {}); })
      .catch(() => { if (alive) setSettings({}); })
      .finally(() => { if (alive) setReady(true); });
    return () => { alive = false; };
  }, []);

  const value = useMemo(() => ({ settings, ready }), [settings, ready]);
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export const useStoreSettings = () => useContext(SettingsContext);
