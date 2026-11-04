/**
 * Hook useMarketIndices for real-time market indices tracking
 * Strictly adheres to < 200 lines limit.
 */

import { useState, useEffect, useCallback } from 'react';
import { MarketIndex } from '../types/market';
import { getInitialMarketIndices, subscribeMarketIndices } from '../services/marketDataService';

interface UseMarketIndicesOptions {
  initialData?: MarketIndex[];
  autoSubscribe?: boolean;
}

export function useMarketIndices(options: UseMarketIndicesOptions = {}) {
  const { initialData, autoSubscribe = true } = options;
  const [indices, setIndices] = useState<MarketIndex[]>(() => initialData || getInitialMarketIndices());
  const [loading, setLoading] = useState<boolean>(!initialData);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<number>(Date.now());

  useEffect(() => {
    if (initialData && initialData.length > 0) {
      setIndices(initialData);
      setLoading(false);
    }
  }, [initialData]);

  useEffect(() => {
    if (!autoSubscribe) return;
    setLoading(false);
    setIsLive(true);

    const unsubscribe = subscribeMarketIndices((updated) => {
      setIndices(updated);
      setLastUpdated(Date.now());
      setError(null);
    });

    return () => {
      unsubscribe();
      setIsLive(false);
    };
  }, [autoSubscribe]);

  const refresh = useCallback(() => {
    try {
      const fresh = getInitialMarketIndices();
      setIndices(fresh);
      setLastUpdated(Date.now());
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi làm mới dữ liệu');
    }
  }, []);

  return {
    indices,
    loading,
    error,
    isLive,
    lastUpdated,
    refresh
  };
}
