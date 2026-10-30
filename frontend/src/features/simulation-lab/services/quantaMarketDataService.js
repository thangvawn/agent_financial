import { fetchInstrumentHistory } from '../../market-portfolio/services/dataHubApi.js'
export function mapPointsToOHLCBars(points = [], interval = '1h') {
  if(!Array.isArray(points)) return []
  const bars=points.map(point=>{
    if(!point) return null
    const raw=point.date ?? point.time
    const ms=typeof raw==='number'?(raw>1e12?raw:raw*1000):Date.parse(raw)
    if(!Number.isFinite(ms)) return null
    const close=Number(point.close ?? point.price),open=Number(point.open ?? close)
    const high=Number(point.high ?? Math.max(open,close)),low=Number(point.low ?? Math.min(open,close))
    if(![open,high,low,close].every(v=>Number.isFinite(v)&&v>0)||high<Math.max(open,close)||low>Math.min(open,close)) return null
    return {time:interval==='1h'?Math.floor(ms/1000):new Date(ms).toISOString().slice(0,10),open,high,low,close,volume:Number(point.volume)||0}
  }).filter(Boolean).sort((a,b)=>a.time>b.time?1:a.time<b.time?-1:0)
  if(bars.some((bar,i)=>i>0&&bar.time===bars[i-1].time)) throw new Error('Nguồn trả nến trùng thời gian; chưa thể mô phỏng.')
  return bars
}
export async function loadQuantaMarketBars(ticker='FPT',period='1y',interval='1d') {
  const rawData=await fetchInstrumentHistory(ticker,{period,interval})
  const bars=mapPointsToOHLCBars(rawData?.points,interval)
  if(!bars.length) throw new Error('Không có dữ liệu lịch sử cho mã và khoảng thời gian đã chọn.')
  const source=rawData.source || 'unknown'
  return {bars,source,asOf:rawData.as_of || null,isReal:!['synthetic','demo','unknown'].includes(source),count:bars.length,
    ticker:ticker.toUpperCase(),firstDate:formatTime(bars[0].time),lastDate:formatTime(bars.at(-1).time),period,interval}
}

const formatTime = value => typeof value === 'number' ? new Date(value*1000).toISOString() : value
