export const barTimestamp = time => typeof time === 'number' ? time*1000 : Date.parse(time)
export function performanceMetrics(equityCurve,trades,capital,{interval='1d',riskFreeRate=0.045}={}) {
  const finalEquity=equityCurve.at(-1)?.equity ?? capital
  const returns=equityCurve.slice(1).map((p,i)=>p.equity/equityCurve[i].equity-1)
  const years=(barTimestamp(equityCurve.at(-1)?.time)-barTimestamp(equityCurve[0]?.time))/(365.25*86400000)
  const periods={ '1d':252,'1wk':52,'1h':1260 }[interval]
  if(!periods) throw new Error('Khung thời gian chưa được hỗ trợ.')
  const rf=(1+riskFreeRate)**(1/periods)-1
  const excess=returns.map(r=>r-rf)
  const mean=excess.length?excess.reduce((a,b)=>a+b,0)/excess.length:0
  const variance=excess.length>1?excess.reduce((a,b)=>a+(b-mean)**2,0)/(excess.length-1):0
  const downside=excess.length?Math.sqrt(excess.reduce((a,b)=>a+Math.min(b,0)**2,0)/excess.length):0
  const varies=returns.length>1 && returns.some(r=>Math.abs(r-returns[0])>1e-12)
  const sharpe=varies&&variance>1e-24?mean/Math.sqrt(variance)*Math.sqrt(periods):null
  const sortino=varies&&downside>1e-12?mean/downside*Math.sqrt(periods):null
  let peak=capital,maxDrawdown=0
  for(const point of equityCurve) { peak=Math.max(peak,point.equity);maxDrawdown=Math.max(maxDrawdown,(peak-point.equity)/peak*100) }
  const wins=trades.filter(t=>t.pnl>0),losses=trades.filter(t=>t.pnl<0)
  const profit=wins.reduce((s,t)=>s+t.pnl,0),loss=-losses.reduce((s,t)=>s+t.pnl,0)
  const winRate=trades.length?wins.length/trades.length*100:0
  const totalReturn=(finalEquity/capital-1)*100
  const profitFactor=loss>0?profit/loss:null
  return {
    total_return:totalReturn,totalReturnPct:totalReturn,cagr:years>0?((finalEquity/capital)**(1/years)-1)*100:null,
    sharpe,sharpeRatio:sharpe,sortino,sortinoRatio:sortino,max_drawdown:maxDrawdown,maxDrawdown,
    win_rate:winRate,winRate,profit_factor:profitFactor,profitFactor,total_trades:trades.length,totalTrades:trades.length,
    winningTrades:wins.length,final_equity:finalEquity,finalEquity,
    avgHoldingDays:trades.length?trades.reduce((s,t)=>s+t.holdingDays,0)/trades.length:0,
    annualizationPeriods:periods,riskFreeRate,
  }
}
