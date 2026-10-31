import { createContext, useContext } from 'react';
export const FinancialWorkflowContext = createContext(null);
const noop = () => {};

export function useFinancialWorkflow() {
  const context = useContext(FinancialWorkflowContext);
  if (!context) {
    return {
      resetWorkflow: noop,
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
