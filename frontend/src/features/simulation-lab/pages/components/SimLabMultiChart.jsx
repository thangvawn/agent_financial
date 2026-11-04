import { useTheme } from '../../../../shared/theme/appTheme';
import { useEffect, useRef } from 'react'
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  ColorType,
  CrosshairMode,
  createSeriesMarkers,
} from 'lightweight-charts';
import { calcEMA } from '../../utils/quantaBacktestSimulator';

const EMPTY_POINTS = []

export default function SimLabMultiChart({
  bars = EMPTY_POINTS,
  ohlcData = EMPTY_POINTS,
  trades = EMPTY_POINTS,
  fastPeriod = 21,
  slowPeriod = 55,
  marketSourceInfo = null,
}) {
  const chartContainerRef = useRef(null);
  const oscContainerRef = useRef(null);
  const { theme } = useTheme();
  const chartsRef = useRef([]);
  const seriesRef = useRef({});
  const data = bars && bars.length > 0 ? bars : ohlcData;

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) return;

    chartContainerRef.current.innerHTML = '';
    if (oscContainerRef.current) oscContainerRef.current.innerHTML = '';

    const width = chartContainerRef.current.clientWidth || 600;

    // Main Chart
    const mainChart = createChart(chartContainerRef.current, {
      width,
      height: 300,
      layout: {
        background: { type: ColorType.Solid, color: '#060c16' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      timeScale: { borderColor: 'rgba(255, 255, 255, 0.08)' },
    });

    const candleSeries = mainChart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candleSeries.setData(
      data.map((b) => ({
        time: b.time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }))
    );

    // Dynamic Fast & Slow EMA overlays
    const fastValues = calcEMA(data, fastPeriod || 21);
    const slowValues = calcEMA(data, slowPeriod || 55);

    const fastSeries = mainChart.addSeries(LineSeries, {
      color: '#06b6d4',
      lineWidth: 2,
      title: 'Fast EMA',
    });
    fastSeries.setData(data.map((b, i) => ({ time: b.time, value: fastValues[i] })));

    const slowSeries = mainChart.addSeries(LineSeries, {
      color: '#f59e0b',
      lineWidth: 2,
      title: 'Slow EMA',
    });
    slowSeries.setData(data.map((b, i) => ({ time: b.time, value: slowValues[i] })));

    // Trade Markers
    if (trades && trades.length > 0) {
      const markers = [];
      trades.forEach((t) => {
        markers.push({
          time: t.entryDate,
          position: 'belowBar',
          color: '#10b981',
          shape: 'arrowUp',
          text: `BUY @${t.entryPrice?.toLocaleString('vi-VN')}`,
        });
        if (t.exitDate) {
          const isWin = (t.pnl || 0) >= 0;
          markers.push({
            time: t.exitDate,
            position: 'aboveBar',
            color: isWin ? '#38bdf8' : '#ef4444',
            shape: 'arrowDown',
            text: `EXIT ${isWin ? '+' : ''}${t.returnPct || t.retPct}%`,
          });
        }
      });
      createSeriesMarkers(candleSeries, markers);
    }

    // Sub-panel Momentum Drift Oscillator
    let oscChart = null;
    if (oscContainerRef.current) {
      oscChart = createChart(oscContainerRef.current, {
        width,
        height: 110,
        layout: {
          background: { type: ColorType.Solid, color: '#040810' },
          textColor: '#94a3b8',
        },
        grid: {
          vertLines: { color: 'rgba(255, 255, 255, 0.02)' },
          horzLines: { color: 'rgba(255, 255, 255, 0.02)' },
        },
        timeScale: { borderColor: 'rgba(255, 255, 255, 0.06)' },
      });

      const histSeries = oscChart.addSeries(HistogramSeries, {
        color: '#8b5cf6',
        title: 'Momentum Drift',
      });
      const histData = data.map((b, i) => {
        const diff = fastValues[i] - slowValues[i];
        return {
          time: b.time,
          value: diff,
          color: diff >= 0 ? '#10b981' : '#ef4444',
        };
      });
      histSeries.setData(histData);
      seriesRef.current = { histogram: histSeries, histogramData: histData };
    }

    const handleResize = () => {
      if (chartContainerRef.current) {
        mainChart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
      if (oscContainerRef.current && oscChart) {
        oscChart.applyOptions({ width: oscContainerRef.current.clientWidth });
      }
    };

    seriesRef.current = { ...seriesRef.current, candle: candleSeries, fast: fastSeries, slow: slowSeries };
    chartsRef.current = [mainChart, oscChart].filter(Boolean);
    applyAppearance(chartsRef.current, chartContainerRef.current, seriesRef.current);
    window.addEventListener('resize', handleResize);
    mainChart.timeScale().fitContent();
    if (oscChart) oscChart.timeScale().fitContent();

    return () => {
      chartsRef.current = [];
      seriesRef.current = {};
      window.removeEventListener('resize', handleResize);
      mainChart.remove();
      if (oscChart) oscChart.remove();
    };
  }, [data, trades, fastPeriod, slowPeriod]);

  useEffect(() => {
    if (chartContainerRef.current) applyAppearance(chartsRef.current, chartContainerRef.current, seriesRef.current);
  }, [theme]);

  return (
    <div className="simlab-chart-wrapper">
      <div className="simlab-chart-head">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">Candora Multi-Panel Chart</span>
          <span className={`simlab-source-pill ${marketSourceInfo?.isReal ? 'real' : 'mock'}`}>
            {marketSourceInfo?.isReal
              ? `● ${marketSourceInfo.source?.toUpperCase()} (${data.length} nến thật${marketSourceInfo.firstDate ? ` • ${marketSourceInfo.firstDate.slice(0, 4)}-${marketSourceInfo.lastDate?.slice(0, 4)}` : ''})`
              : '● Dữ liệu mẫu học tập'}
          </span>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono">
          <span className="text-cyan-300">● Fast EMA ({fastPeriod})</span>
          <span className="text-amber-400">● Slow EMA ({slowPeriod})</span>
          <span className="text-emerald-400">▲ Buy</span>
          <span className="text-rose-400">▼ Exit</span>
        </div>
      </div>

      <div
        ref={chartContainerRef}
        className="simlab-chart-main"
        style={{ width: '100%', minHeight: '300px', height: '300px' }}
      />
      <div
        ref={oscContainerRef}
        className="simlab-chart-sub"
        style={{ width: '100%', minHeight: '110px', height: '110px', marginTop: '8px' }}
      />
    </div>
  );
}

// Read shared CSS tokens; changing theme updates appearance without resetting chart time ranges.
function applyAppearance(charts, element, series) {
  const style = getComputedStyle(element);
  const token = name => style.getPropertyValue(name).trim();
  series.candle?.applyOptions({ upColor: token('--pos'), downColor: token('--neg'), wickUpColor: token('--pos'), wickDownColor: token('--neg') });
  series.fast?.applyOptions({ color: token('--accent') });
  series.slow?.applyOptions({ color: token('--warn') });
  if (series.histogram) series.histogram.setData(series.histogramData.map(point => ({ ...point, color: token(point.value >= 0 ? '--pos' : '--neg') })));
  for (const chart of charts) chart.applyOptions({
    layout: { background: { type: ColorType.Solid, color: token('--surface') }, textColor: token('--ink-muted') },
    grid: { vertLines: { color: token('--line-subtle') }, horzLines: { color: token('--line-subtle') } },
    timeScale: { borderColor: token('--line') }, rightPriceScale: { borderColor: token('--line') },
  });
}
