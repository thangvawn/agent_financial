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
  const [error, setError] = useState('');
  const requestRef = useRef(0);
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
    setError(''); setSimulationResult(null);
    try {
      setSimulationResult(runDeterministicBacktest(quantaCode, parseQuantaParams(quantaCode), bars, { interval }));
    } catch (reason) { setError(reason.message); }
    finally { setIsRunning(false); }
  }, [quantaCode, interval]);

  useEffect(() => {
    const request = ++requestRef.current;
    let cancelled = false;
    setIsRunning(true); setError(''); setSimulationResult(null); setMarketSourceInfo(null);
    currentBarsRef.current = [];
    loadQuantaMarketBars(ticker, period, interval).then(feed => {
      if (cancelled || request !== requestRef.current) return;
      currentBarsRef.current = feed.bars;
      setMarketSourceInfo(feed);
      executeBacktestWithBars(feed.bars);
    }).catch(reason => {
      if (!cancelled && request === requestRef.current) { setError(reason.message); setIsRunning(false); }
    });
    return () => { cancelled = true; };
  }, [ticker, period, interval, executeBacktestWithBars]);

  const handleManualReRun = () => {
    setIsRunning(true);
    executeBacktestWithBars(currentBarsRef.current);
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

      {error && <p role="alert" className="simlab-error">{error}</p>}
      <p className="simlab-assumptions">Mô phỏng: tín hiệu cuối nến, khớp ở giá mở cửa nến kế tiếp; lô 100 cp, phí mua 0,15%, phí và thuế bán 0,25%; chưa tính trượt giá. Giữ ít nhất hai phiên có dữ liệu trước khi bán. Dữ liệu tuần chỉ kiểm tra tại các phiên quan sát được.</p>
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
