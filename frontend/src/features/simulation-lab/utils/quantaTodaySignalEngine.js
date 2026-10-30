import { ema } from './quantaIndicators.js'
import { roundToVnPriceTick, calculatePriceBands, checkLiquidityStatus } from './quantaVnMarketRules.js'
export function computeTodaySignal({ bars=[], params={}, trades=[], openPosition=null, strategy=null, context={} }) {
  if(bars.length<10) return null
  const latest=bars.at(-1),currentPrice=latest.close
  const position=openPosition || trades.findLast(t=>!t.exitDate) || null
  const fastLen=Number(params.fast_len ?? params.fast_period ?? 21),slowLen=Number(params.slow_len ?? params.slow_period ?? 55)
  let signal=null
  if(strategy) signal=bars.length>strategy.warmup?strategy.signal(bars.length-1,{...context,position:Boolean(position)}):null
  else if(bars.length>Math.max(fastLen,slowLen)) {
    const closes=bars.map(b=>b.close),fast=ema(closes,fastLen),slow=ema(closes,slowLen)
    if(!position&&fast.at(-1)>slow.at(-1)&&fast.at(-2)<=slow.at(-2)) signal={side:'buy'}
    if(position&&fast.at(-1)<slow.at(-1)&&fast.at(-2)>=slow.at(-2)) signal={side:'sell'}
  }
  const action=signal?.side==='buy'?'BUY':signal?.side==='sell'?'SELL':position?'HOLD':'WAIT'
  const base=position?.entryPrice ?? currentPrice
  const stopPct=params.stop_loss_pct ?? params.stop_loss ?? null
  const takePct=params.take_profit_pct ?? null
  return {action,actionLabel:{BUY:'TÍN HIỆU MUA MÔ PHỎNG',SELL:'TÍN HIỆU THOÁT MÔ PHỎNG',HOLD:'ĐANG GIỮ VỊ THẾ',WAIT:'CHỜ TÍN HIỆU'}[action],
    color:{BUY:'emerald',SELL:'rose',HOLD:'amber',WAIT:'slate'}[action],asOfDate:latest.time,currentPrice:roundToVnPriceTick(currentPrice),
    stopLossPrice:stopPct===null?null:roundToVnPriceTick(base*(1-stopPct/100)),takeProfitPrice:takePct===null?null:roundToVnPriceTick(base*(1+takePct/100)),
    confidenceScore:null,riskRewardRatio:stopPct>0&&takePct!==null?takePct/stopPct:null,
    rationale:signal?'Điều kiện chiến lược thỏa mãn ở nến cuối; lệnh mô phỏng thực hiện ở nến kế tiếp khi đủ điều kiện thanh toán.':position?'Vị thế mô phỏng còn mở.':'Chưa có giao cắt hoặc điều kiện chiến lược mới.',
    bands:calculatePriceBands(bars.at(-2).close),liquidity:checkLiquidityStatus(bars)}
}
