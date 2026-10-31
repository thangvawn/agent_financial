import { parseExpression, applyBinary } from './quantaExpression.js'
import { indicator } from './quantaIndicators.js'
export function emaStrategy(params={}) {
  return `strategy "EMA Cross"\nparams:\n  fast_len: ${params.fast_len ?? params.fast_period ?? 20}\n  slow_len: ${params.slow_len ?? params.slow_period ?? 50}\ndetect:\n  fast = ema(market.close, fast_len)\n  slow = ema(market.close, slow_len)\nact:\n  when fast crossover slow and not position.is_long:\n    enter long with wnav 95pct\n  when fast crossunder slow and position.is_long:\n    close long`
}
export function compileStrategy(code,bars) {
  if(code.length>20000) throw new Error('Chiến lược quá dài.')
  const params=Object.create(null),definitions=Object.create(null),rules=[]
  let section='',pending=null,warmup=2
  const sections=new Set(['params','detect','act','render','score'])
  for(const raw of code.split('\n')) {
    const line=raw.trim();if(!line||line.startsWith('#')) continue
    if(/^strategy\s+"[^"]+"$/.test(line)||/^@(watchlist|timeframe|regime|style)\s+"[^"]+"$/.test(line)) continue
    const header=line.match(/^(\w+):$/)
    if(header) {if(!sections.has(header[1])) throw new Error(`Khối chưa hỗ trợ: ${header[1]}`);section=header[1];continue}
    if(section==='render'||section==='score') continue // presentation-only; referenced undefined scores are rejected below
    if(section==='params') {
      const m=line.match(/^(\w+)\s*(?:=|:)\s*(\d+(?:\.\d+)?)(?:pct|bps|d)?(?:\s+in\s+\[(\d+(?:\.\d+)?)(?:pct|bps|d)?\.\.(\d+(?:\.\d+)?)(?:pct|bps|d)?\])?$/)
      if(!m||Object.hasOwn(params,m[1])) throw new Error(`Tham số không hợp lệ: ${line}`)
      const v=Number(m[2]);if(!Number.isFinite(v)||(m[3]&&(v<Number(m[3])||v>Number(m[4])))) throw new Error(`Tham số ngoài giới hạn: ${line}`)
      params[m[1]]=v;continue
    }
    if(section==='detect') {
      const m=line.match(/^(\w+)\s*=\s*(.+)$/)
      if(!m||Object.hasOwn(definitions,m[1])||Object.hasOwn(params,m[1])) throw new Error(`Khai báo không hợp lệ: ${line}`)
      definitions[m[1]]=parseExpression(m[2]);continue
    }
    if(section==='act') {
      if(line.startsWith('when ')&&line.endsWith(':')) {if(pending) throw new Error('Thiếu hành động.');pending=parseExpression(line.slice(5,-1));continue}
      const entry=line.match(/^enter long with (?:size|wnav) (\w+(?:\.\d+)?)(?: tag "[^"]*")?$/)
      if(entry&&pending) {
        const value=/^\d/.test(entry[1])?entry[1].replace(/pct$/,''):entry[1];const allocation=Object.hasOwn(params,value)?params[value]:Number(value)
        if(!Number.isFinite(allocation)||allocation<=0||allocation>100) throw new Error('Tỷ trọng phải lớn hơn 0 và không quá 100%.')
        rules.push({condition:pending,side:'buy',allocation:allocation/100});pending=null;continue
      }
      if(/^close long(?: tag "[^"]*")?$/.test(line)&&pending) {rules.push({condition:pending,side:'sell'});pending=null;continue}
    }
    throw new Error(`Cú pháp chưa hỗ trợ: ${line}`)
  }
  if(pending||!rules.some(r=>r.side==='buy')||!rules.some(r=>r.side==='sell')) throw new Error('Chiến lược phải có điều kiện mua và bán hợp lệ.')
  const functions={ema:2,sma:2,rsi:2,atr:4,bbands:3,donchian:3}
  const visiting=new Set(),visited=new Set()
  function validate(node,dynamic=false) {
    if(node.type==='ref') {
      if(['true','false','market'].includes(node.name)||Object.hasOwn(params,node.name)) return
      if(['position','gain','loss','drawdown_from_peak'].includes(node.name)) {if(!dynamic) throw new Error('Vị thế chỉ được dùng trong điều kiện hành động.');return}
      if(!definitions[node.name]) throw new Error(`Biến chưa hỗ trợ: ${node.name}`)
      if(visiting.has(node.name)) throw new Error('Biến phụ thuộc vòng lặp.')
      if(!visited.has(node.name)) {visiting.add(node.name);validate(definitions[node.name]);visiting.delete(node.name);visited.add(node.name)}
    }
    if(node.type==='call') {
      if(functions[node.name]!==node.args.length) throw new Error(`Hàm chưa hỗ trợ hoặc sai số đối số: ${node.name}`)
      node.args.forEach(arg=>validate(arg,false))
    } else {
      for(const child of [node.arg,node.left,node.right].filter(Boolean)) validate(child,dynamic)
    }
  }
  Object.values(definitions).forEach(node=>validate(node))
  rules.forEach(rule=>validate(rule.condition,true))
  const cache=new Map(),definitionCache=new Map()
  function evaluate(node,i,context={}) {
    if(i<0||i>=bars.length) return null
    if(node.type==='number') return node.value
    if(node.type==='ref') {
      if(node.name==='market') return bars[i]
      if(node.name==='position') return {is_long:Boolean(context.position)}
      if(node.name==='true'||node.name==='false') return node.name==='true'
      if(Object.hasOwn(params,node.name)) return params[node.name]
      if(['gain','loss','drawdown_from_peak'].includes(node.name)) return context[node.name] ?? null
      const key=`${node.name}:${i}`
      if(!definitionCache.has(key)) definitionCache.set(key,evaluate(definitions[node.name],i,context))
      return definitionCache.get(key)
    }
    if(node.type==='property') return evaluate(node.arg,i,context)?.[node.key] ?? null
    if(node.type==='history') return evaluate(node.arg,i-node.shift,context)
    if(node.type==='unary') {const v=evaluate(node.arg,i,context);return node.op==='not'?(v===null?null:!v):Number.isFinite(v)?-v:null}
    if(node.type==='binary') return applyBinary(node.op,evaluate(node.left,i,context),evaluate(node.right,i,context),node.op.startsWith('cross')?evaluate(node.left,i-1,context):null,node.op.startsWith('cross')?evaluate(node.right,i-1,context):null)
    if(!cache.has(node)) {
      const args=node.args.map(arg=>bars.map((_,j)=>evaluate(arg,j)))
      const period=args[{ema:1,sma:1,rsi:1,atr:3,bbands:1,donchian:2}[node.name]][0]
      if (!Number.isInteger(period)) throw new Error('Chu kỳ chỉ báo không hợp lệ.')
      cache.set(node,indicator(node.name,args))
    }
    return cache.get(node)[i]
  }
  // Materialize indicator caches before choosing the warm-up boundary.
  Object.values(definitions).forEach(node=>evaluate(node,bars.length-1))
  rules.forEach(r=>evaluate(r.condition,bars.length-1,{}))
  const lookbacks = new Map()
  function lookback(node) {
    if (lookbacks.has(node)) return lookbacks.get(node)
    let required = 0
    if (node.type === 'ref' && definitions[node.name]) required = lookback(definitions[node.name])
    else if (node.type === 'history') required = lookback(node.arg) + node.shift
    else if (node.type === 'property' || node.type === 'unary') required = lookback(node.arg)
    else if (node.type === 'binary') required = Math.max(lookback(node.left), lookback(node.right)) + (node.op.startsWith('cross') ? 1 : 0)
    else if (node.type === 'call') {
      const periodIndex = {ema:1,sma:1,rsi:1,atr:3,bbands:1,donchian:2}[node.name]
      const period = evaluate(node.args[periodIndex], 0)
      required = Math.max(...node.args.slice(0,periodIndex).map(lookback)) + period - (node.name === 'rsi' ? 0 : 1)
    }
    lookbacks.set(node, required)
    return required
  }
  warmup = Math.max(warmup, ...rules.map(rule => lookback(rule.condition)))
  return { params, warmup, signal(i,context={}) {if(i<warmup) return null;return rules.find(r=>Boolean(evaluate(r.condition,i,context))&&(r.side==='buy'?!context.position:context.position)) || null} }
}
