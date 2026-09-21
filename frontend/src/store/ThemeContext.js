import React from 'react';

const ThemeContext = React.createContext({ theme: 'light', toggle: () => {}, setTheme: () => {} });

const STORAGE_KEY = 'cp:theme:v1';

const getInitialTheme = () => {
  if (typeof window === 'undefined') return 'light';
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch (e) {
    /* ignore */
  }
  // Default: light (brand default). We intentionally do NOT auto-follow OS.
  return 'light';
};

export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = React.useState(getInitialTheme);

  // Apply/remove the `cp-dark` class on <html>. Only .cp-store subtrees react to it,
  // so the /admin backoffice keeps its own styling.
  React.useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') root.classList.add('cp-dark');
    else root.classList.remove('cp-dark');
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      /* ignore */
    }
  }, [theme]);

  const setTheme = React.useCallback((t) => setThemeState(t === 'dark' ? 'dark' : 'light'), []);
  const toggle = React.useCallback(() => setThemeState((t) => (t === 'dark' ? 'light' : 'dark')), []);

  const value = React.useMemo(() => ({ theme, toggle, setTheme }), [theme, toggle, setTheme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => React.useContext(ThemeContext);
