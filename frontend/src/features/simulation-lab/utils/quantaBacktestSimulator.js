import { computeTodaySignal } from './quantaTodaySignalEngine.js'
import { ema } from './quantaIndicators.js'
import { compileStrategy, emaStrategy } from './quantaStrategy.js'
import { performanceMetrics, barTimestamp } from './quantaMetrics.js'

export function generateSyntheticOHLCV(ticker = 'FPT', numBars = 180) {
  const bars = []
  const basePrices = { FPT: 135000, VNM: 68000, HPG: 26000, SSI: 32000, VCB: 91000, VIC: 43000 }
  let currentPrice = basePrices[ticker] || 50000
  const now = new Date('2026-10-10')

  for (let i = numBars; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i * 1.4)
    if (d.getDay() === 0 || d.getDay() === 6) continue

    const change = (Math.sin(i * 0.15) * 0.015 + (Math.sin(i * 0.3) * 0.01))
    const open = Math.round(currentPrice)
    const close = Math.round(open * (1 + change))
    const high = Math.round(Math.max(open, close) * (1 + Math.abs(Math.cos(i)) * 0.012))
    const low = Math.round(Math.min(open, close) * (1 - Math.abs(Math.sin(i)) * 0.012))
    const volume = Math.round(800000 + Math.abs(Math.sin(i * 0.5)) * 1200000)

    const dateStr = d.toISOString().split('T')[0]
    bars.push({ time: dateStr, open, high, low, close, volume })
    currentPrice = close
  }
  return bars
}


export const calcEMA = (data, length) => ema(data.map(b => b.close), length)
export const calculateEMA = ema
export const generateSampleOHLC = generateSyntheticOHLCV

export function runQuantaSimulation({ params = {}, bars, code = '', interval = '1d' }) {
  if (!Array.isArray(bars) || bars.length < 2) throw new Error('Chưa đủ dữ liệu lịch sử để mô phỏng.')
  const data = bars.map(bar => ({ ...bar }))
  data.forEach((bar,i) => {
    if (![bar.open,bar.high,bar.low,bar.close].every(v=>Number.isFinite(v)&&v>0) || !Number.isFinite(barTimestamp(bar.time)) || (i && barTimestamp(bar.time)<=barTimestamp(data[i-1].time))) throw new Error('Dữ liệu nến không hợp lệ hoặc trùng thời gian.')
  })
  const strategy = compileStrategy(code.trim() || emaStrategy(params), data)
  if (data.length <= strategy.warmup) throw new Error(`Cần ít nhất ${strategy.warmup+1} nến lịch sử cho chiến lược này; hiện có ${data.length}.`)
  const capital=100000000, buyFee=0.0015, sellFee=0.0025
  let cash=capital,position=null,pending=null,session=0,previousDay=''
  const trades=[],equityCurve=[]
  function context(price) {
    const gain=position?(price/position.entryPrice-1)*100:null
    return {position: Boolean(position),gain,loss: gain===null?null:-gain,drawdown_from_peak:position?(1-price/position.peak)*100:null}
  }
  for(let i=0;i<data.length;i++) {
    const bar=data[i],day=new Date(barTimestamp(bar.time)).toISOString().slice(0,10)
    if(day!==previousDay) {session++;previousDay=day}
    // A close signal may execute only at the next observed open, never on its own close.
    if(pending?.side==='buy'&&!position) {
      const shares=Math.floor(cash*pending.allocation/(bar.open*(1+buyFee)*100))*100
      if(shares>0) {
        const cost=shares*bar.open*(1+buyFee)
        cash-=cost;position={shares,entryPrice:bar.open,entryDate:bar.time,entryIndex:i,entrySession:session,cost,peak:bar.open}
      }
    } else if(pending?.side==='sell'&&position&&session-position.entrySession>=2) {
      const proceeds=position.shares*bar.open*(1-sellFee),pnl=proceeds-position.cost
      cash+=proceeds
      trades.push({id:`TR-${trades.length+1}`,type:'LONG',entryDate:position.entryDate,entryPrice:position.entryPrice,
        exitDate:bar.time,exitPrice:bar.open,shares:position.shares,volume:position.shares,pnl,
        retPct:pnl/position.cost*100,returnPct:pnl/position.cost*100,barsHeld:i-position.entryIndex,
        holdingDays:(barTimestamp(bar.time)-barTimestamp(position.entryDate))/86400000,
        entryFee:position.shares*position.entryPrice*buyFee,exitFee:position.shares*bar.open*sellFee})
      position=null
    }
    // Keep a requested exit pending while the position is unsettled.
    const unsettledExit=pending?.side==='sell'&&position&&session-position.entrySession<2
    if(position) position.peak=Math.max(position.peak,bar.close)
    pending=unsettledExit?pending:i>=strategy.warmup?strategy.signal(i,context(bar.close)):null
    equityCurve.push({time:bar.time,equity:cash+(position?.shares||0)*bar.close,benchmark:capital*bar.close/data[0].close,close:bar.close})
  }
  const openPosition=position?{...position,unrealizedPnl:position.shares*data.at(-1).close-position.cost}:null
  const todaySignal=computeTodaySignal({bars:data,params:strategy.params,openPosition,strategy,context:context(data.at(-1).close)})
  const markers=trades.flatMap(t=>[{time:t.entryDate,position:'belowBar',color:'#10b981',shape:'arrowUp',text:'BUY'},{time:t.exitDate,position:'aboveBar',color:'#ef4444',shape:'arrowDown',text:'SELL'}])
  if(openPosition) markers.push({time:openPosition.entryDate,position:'belowBar',color:'#10b981',shape:'arrowUp',text:'BUY'})
  return {metrics:performanceMetrics(equityCurve,trades,capital,{interval}),trades,markers,equityCurve,bars:data,ohlc:data,todaySignal,openPosition,
    assumptions:{execution:'next_bar_open',buyFee,sellFee,settlement:'2 observed trading sessions',slippage:0,interval}}
}
export const runDeterministicBacktest = (code, params, bars, options={}) => runQuantaSimulation({code,params,bars,...options})
