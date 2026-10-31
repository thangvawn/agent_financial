import React, { useState, useCallback } from 'react';
import { FinancialWorkflowContext } from './FinancialWorkflowContext';

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

  const resetWorkflow = useCallback(() => {
    setActiveTicker('FPT'); setPreloadedStrategyCode(null); setSelectedPeriod('1y'); setSelectedInterval('1d');
    setPopoverState({isOpen:false,ticker:'',x:0,y:0});
  }, []);

  const value = {
    resetWorkflow,
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

