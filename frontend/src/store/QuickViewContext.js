import { createContext, useContext } from 'react';

export const QuickViewContext = createContext({
  openQuickView: () => {},
});

export const useQuickView = () => useContext(QuickViewContext);
