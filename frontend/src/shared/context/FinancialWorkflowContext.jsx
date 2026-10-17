import React, { createContext, useContext, useState, useCallback } from 'react';

const FinancialWorkflowContext = createContext(null);

export function FinancialWorkflowProvider({ children, onNavigateView }) {
  const [activeTicker, setActiveTicker] = useState('FPT');
  const [preloadedStrategyCode, setPreloadedStrategyCode] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('1y');
  const [selectedInterval, setSelectedInterval] = useState('1d');
  const [popoverState, setPopoverState] = useState({
    isOpen: false,
    ticker: '',
    x: 0,
    y: 0,
  });

  const navigateToSimulationLab = useCallback(
    ({ ticker, strategyCode = null, period = '1y', interval = '1d' }) => {
      const cleanTicker = (ticker || activeTicker || 'FPT').toUpperCase();
      setActiveTicker(cleanTicker);
      if (strategyCode) setPreloadedStrategyCode(strategyCode);
      if (period) setSelectedPeriod(period);
      if (interval) setSelectedInterval(interval);

      if (onNavigateView) {
        onNavigateView('pro_lab');
      }
    },
    [activeTicker, onNavigateView]
  );

  const navigateToBctc = useCallback(
    (ticker) => {
      const cleanTicker = (ticker || activeTicker || 'FPT').toUpperCase();
      setActiveTicker(cleanTicker);
      if (onNavigateView) {
        onNavigateView('guided_investing');
      }
    },
    [activeTicker, onNavigateView]
  );

  const navigateToMarket = useCallback(
    (ticker) => {
      const cleanTicker = (ticker || activeTicker || 'FPT').toUpperCase();
      setActiveTicker(cleanTicker);
      if (onNavigateView) {
        onNavigateView('global_terminal');
      }
    },
    [activeTicker, onNavigateView]
  );

  const openTickerMenu = useCallback((ticker, event) => {
    if (event) event.stopPropagation();
    const rect = event?.currentTarget?.getBoundingClientRect();
    setPopoverState({
      isOpen: true,
      ticker: (ticker || 'FPT').toUpperCase(),
      x: rect ? Math.round(rect.left + rect.width / 2) : 200,
      y: rect ? Math.round(rect.bottom + 6) : 200,
    });
  }, []);

  const closeTickerMenu = useCallback(() => {
    setPopoverState((prev) => ({ ...prev, isOpen: false }));
  }, []);

  const value = {
    activeTicker,
    setActiveTicker,
    preloadedStrategyCode,
    setPreloadedStrategyCode,
    selectedPeriod,
    setSelectedPeriod,
    selectedInterval,
    setSelectedInterval,
    popoverState,
    openTickerMenu,
    closeTickerMenu,
    navigateToSimulationLab,
    navigateToBctc,
    navigateToMarket,
  };

  return (
    <FinancialWorkflowContext.Provider value={value}>
      {children}
    </FinancialWorkflowContext.Provider>
  );
}

export function useFinancialWorkflow() {
  const context = useContext(FinancialWorkflowContext);
  if (!context) {
    return {
      activeTicker: 'FPT',
      setActiveTicker: () => {},
      preloadedStrategyCode: null,
      setPreloadedStrategyCode: () => {},
      selectedPeriod: '1y',
      setSelectedPeriod: () => {},
      selectedInterval: '1d',
      setSelectedInterval: () => {},
      popoverState: { isOpen: false, ticker: '', x: 0, y: 0 },
      openTickerMenu: () => {},
      closeTickerMenu: () => {},
      navigateToSimulationLab: () => {},
      navigateToBctc: () => {},
      navigateToMarket: () => {},
    };
  }
  return context;
}
