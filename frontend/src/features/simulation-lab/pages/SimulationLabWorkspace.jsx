import React, { useState, useEffect, useCallback, useRef } from 'react';
import SimLabHeader from './components/SimLabHeader';
import QuantaWorkshopEditor from './components/QuantaWorkshopEditor';
import QuantaParamSliders from './components/QuantaParamSliders';
import SimLabMultiChart from './components/SimLabMultiChart';
import SimLabTearsheet from './components/SimLabTearsheet';
import SimLabVisualBuilder from './components/SimLabVisualBuilder';
import SimLabAiCopilotModal from './components/SimLabAiCopilotModal';
import SimLabTodaySignalBanner from './components/SimLabTodaySignalBanner';
import SimLabBlueprintModal from './components/SimLabBlueprintModal';
import { DEFAULT_QUANTA_CODE } from '../content/quantaStrategyPresets';
import { runDeterministicBacktest } from '../utils/quantaBacktestSimulator';
import { parseQuantaParams } from '../utils/quantaParamParser';
import { loadQuantaMarketBars } from '../services/quantaMarketDataService';
import { useFinancialWorkflow } from '../../../shared/context/FinancialWorkflowContext';

import './styles/simlab-studio.css';
import './styles/simlab-editor.css';
import './styles/simlab-chart.css';
import './styles/simlab-builder.css';
import './styles/simlab-feed.css';

export default function SimulationLabWorkspace() {
  const workflow = useFinancialWorkflow();
  const [ticker, setTicker] = useState(workflow.activeTicker || 'FPT');
  const [interval, setInterval] = useState(workflow.selectedInterval || '1d');
  const [period, setPeriod] = useState(workflow.selectedPeriod || '1y');
  const [mode, setMode] = useState('studio');
  const [quantaCode, setQuantaCode] = useState(workflow.preloadedStrategyCode || DEFAULT_QUANTA_CODE);
  const [isRunning, setIsRunning] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isBlueprintModalOpen, setIsBlueprintModalOpen] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);
  const [marketSourceInfo, setMarketSourceInfo] = useState(null);
  const currentBarsRef = useRef([]);

  useEffect(() => {
    if (workflow.activeTicker && workflow.activeTicker !== ticker) {
      setTicker(workflow.activeTicker);
    }
    if (workflow.preloadedStrategyCode) {
      setQuantaCode(workflow.preloadedStrategyCode);
      workflow.setPreloadedStrategyCode(null);
    }
  }, [workflow.activeTicker, workflow.preloadedStrategyCode]);

  const executeBacktestWithBars = useCallback((bars) => {
    setIsRunning(true);
    const parsed = parseQuantaParams(quantaCode);
    const res = runDeterministicBacktest(quantaCode, parsed, bars);
    setSimulationResult(res);
    setIsRunning(false);
  }, [quantaCode]);

  const loadDataAndRun = useCallback(async () => {
    setIsRunning(true);
    const feed = await loadQuantaMarketBars(ticker, period, interval);
    currentBarsRef.current = feed.bars;
    setMarketSourceInfo({
      source: feed.source,
      isReal: feed.isReal,
      count: feed.count,
      ticker: feed.ticker,
      firstDate: feed.firstDate,
      lastDate: feed.lastDate,
      interval,
      period,
    });
    executeBacktestWithBars(feed.bars);
  }, [ticker, period, interval, executeBacktestWithBars]);

  useEffect(() => {
    loadDataAndRun();
  }, [loadDataAndRun]);

  const handleManualReRun = () => {
    if (currentBarsRef.current.length > 0) {
      executeBacktestWithBars(currentBarsRef.current);
    } else {
      loadDataAndRun();
    }
  };

  const handleLoadBlueprint = (bp) => {
    if (!bp) return;
    setTicker(bp.ticker || ticker);
    setPeriod(bp.period || period);
    setInterval(bp.interval || interval);
    setQuantaCode(bp.code || quantaCode);
  };

  return (
    <div className="quanta-simulation-lab">
      <SimLabHeader
        ticker={ticker}
        setTicker={setTicker}
        interval={interval}
        setInterval={setInterval}
        period={period}
        setPeriod={setPeriod}
        mode={mode}
        setMode={setMode}
        onRun={handleManualReRun}
        isRunning={isRunning}
        marketSourceInfo={marketSourceInfo}
        onOpenCopilot={() => setIsCopilotOpen(true)}
        onOpenBlueprintModal={() => setIsBlueprintModalOpen(true)}
      />

      <main className="simlab-main-workspace">
        {mode === 'studio' && (
          <div className="studio-split-view">
            <div className="studio-left-panel">
              <QuantaWorkshopEditor
                code={quantaCode}
                onChange={setQuantaCode}
                onApplyPreset={(p) => setQuantaCode(p.code)}
                onRunBacktest={handleManualReRun}
              />
              <QuantaParamSliders code={quantaCode} onChangeCode={setQuantaCode} />
            </div>

            <div className="studio-right-panel">
              <SimLabTodaySignalBanner todaySignal={simulationResult?.todaySignal} ticker={ticker} />
              <SimLabMultiChart
                bars={simulationResult?.ohlc}
                trades={simulationResult?.trades}
                fastPeriod={parseQuantaParams(quantaCode).fast_period}
                slowPeriod={parseQuantaParams(quantaCode).slow_period}
                marketSourceInfo={marketSourceInfo}
              />
              <SimLabTearsheet
                metrics={simulationResult?.metrics}
                trades={simulationResult?.trades}
              />
            </div>
          </div>
        )}

        {mode === 'visual' && (
          <SimLabVisualBuilder
            onApplyToQuantaCode={(code) => {
              setQuantaCode(code);
              setMode('studio');
            }}
          />
        )}

        {mode === 'tearsheet' && (
          <SimLabTearsheet
            metrics={simulationResult?.metrics}
            trades={simulationResult?.trades}
          />
        )}
      </main>

      {isCopilotOpen && (
        <SimLabAiCopilotModal
          code={quantaCode}
          onClose={() => setIsCopilotOpen(false)}
          onApplyOptimizedCode={(newCode) => {
            setQuantaCode(newCode);
            setIsCopilotOpen(false);
          }}
          metrics={simulationResult?.metrics}
          ticker={ticker}
        />
      )}

      <SimLabBlueprintModal
        isOpen={isBlueprintModalOpen}
        onClose={() => setIsBlueprintModalOpen(false)}
        currentConfig={{
          ticker,
          period,
          interval,
          code: quantaCode,
          params: parseQuantaParams(quantaCode),
          metrics: simulationResult?.metrics,
        }}
        onLoadBlueprint={handleLoadBlueprint}
      />
    </div>
  );
}
