import { runQuantaSimulation } from '../../frontend/src/features/simulation-lab/utils/quantaBacktestSimulator.js'
import { compileStrategy } from '../../frontend/src/features/simulation-lab/utils/quantaStrategy.js'
import { rsi, sma } from '../../frontend/src/features/simulation-lab/utils/quantaIndicators.js'
import { writeFile } from 'node:fs/promises'
const bars=Array.from({length:50},(_,i)=>({time:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),open:10000,high:10100,low:9900,close:10000,volume:100000}))
const code=condition=>`strategy "QA"\ndetect:\n  bullish = market.close > 9000\nact:\n  when ${condition} and not position.is_long:\n    enter long with wnav 50pct\n  when position.is_long and market.close < 1:\n    close long`
const plain=runQuantaSimulation({bars,code:code('bullish')})
const compared=runQuantaSimulation({bars,code:code('bullish == true')})
const historicalCode=code('not (market.close > market.close[100])')
const history=runQuantaSimulation({bars,code:historicalCode})
const smoothed=sma(bars.map(b=>b.close),5)
const indicator=rsi(smoothed,5)
const evidence={
 boolean_equality:{plain_entry:plain.openPosition?.entryDate??null,equivalent_boolean_comparison_entry:compared.openPosition?.entryDate??null},
 history_warmup:{bars:bars.length,required_history:100,reported_warmup:compileStrategy(historicalCode,bars).warmup,actual_entry:history.openPosition?.entryDate??null},
 nested_rsi:{constant_close:10000,sma_first_values:smoothed.slice(0,8),rsi_after_full_warmup:indicator[15],expected_for_flat_series:50},
}
await writeFile('output/playwright/review-2026-10-31/math-evidence.json',JSON.stringify(evidence,null,2))
console.log(JSON.stringify(evidence,null,2))

process.exitCode=(
 plain.openPosition?.entryDate!==compared.openPosition?.entryDate
 || history.openPosition!==null
 || indicator[15]!==50
)?1:0
