export function ema(values, length) {
  const k = 2 / (length + 1)
  let previous = null
  return values.map(value => {
    if (!Number.isFinite(value)) return null
    previous = previous === null ? value : value*k + previous*(1-k)
    return previous
  })
}
export function rolling(values, length, reduce) {
  return values.map((_,i) => {
    if (i < length-1) return null
    const window = values.slice(i-length+1,i+1)
    return window.every(Number.isFinite) ? reduce(window) : null
  })
}
export const sma = (values, length) => rolling(values,length,v=>v.reduce((a,b)=>a+b,0)/length)
export function rsi(values, length) {
  let gain=0, loss=0
  return values.map((v,i) => {
    if (!i) return null
    const d=v-values[i-1], g=Math.max(0,d), l=Math.max(0,-d)
    if (i<=length) { gain+=g/length; loss+=l/length }
    else { gain=(gain*(length-1)+g)/length; loss=(loss*(length-1)+l)/length }
    if(i<length) return null
    return loss===0 ? (gain===0 ? 50 : 100) : 100-100/(1+gain/loss)
  })
}
export function atr(high,low,close,length) {
  const tr=high.map((h,i)=>Math.max(h-low[i],i?Math.abs(h-close[i-1]):0,i?Math.abs(low[i]-close[i-1]):0))
  let previous=null
  return tr.map((v,i)=>{
    if(i<length-1) return null
    previous=previous===null?tr.slice(0,length).reduce((a,b)=>a+b,0)/length:(previous*(length-1)+v)/length
    return previous
  })
}
export function indicator(name,args) {
  const periodIndex={ema:1,sma:1,rsi:1,atr:3,bbands:1,donchian:2}[name]
  if(periodIndex===undefined) throw new Error(`Hàm chưa hỗ trợ: ${name}`)
  const n=args[periodIndex][0]
  if(!Number.isInteger(n)||n<1||n>2000||!args[periodIndex].every(v=>v===n)) throw new Error('Chu kỳ chỉ báo phải là số nguyên từ 1 đến 2000.')
  if(name==='ema') return ema(args[0],n)
  if(name==='sma') return sma(args[0],n)
  if(name==='rsi') return rsi(args[0],n)
  if(name==='atr') return atr(args[0],args[1],args[2],n)
  if(name==='donchian') {
    const upper=rolling(args[0],n,v=>Math.max(...v)), lower=rolling(args[1],n,v=>Math.min(...v))
    return upper.map((v,i)=>({upper:v,lower:lower[i]}))
  }
  const multiple=args[2]?.[0]
  if(!Number.isFinite(multiple)||multiple<=0) throw new Error('Độ rộng Bollinger không hợp lệ.')
  const mean=sma(args[0],n)
  const deviation=rolling(args[0],n,v=>{const m=v.reduce((a,b)=>a+b,0)/n;return Math.sqrt(v.reduce((a,b)=>a+(b-m)**2,0)/n)})
  return mean.map((v,i)=>({middle:v,upper:v===null?null:v+multiple*deviation[i],lower:v===null?null:v-multiple*deviation[i]}))
}
