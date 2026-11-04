import { useMemo } from 'react'
import { IndexSparklineCard } from './IndexSparklineCard'
import './sonar-cards.css'

const INDEX_GROUPS = [
  { symbols: ['VNINDEX'], label: 'VN-INDEX' },
  { symbols: ['VN30'], label: 'VN30' },
  { symbols: ['HNX30', 'HNXINDEX30', 'HNXINDEX'], label: 'HNX' },
  { symbols: ['UPCOMINDEX', 'UPCOM'], label: 'UPCOM' },
]

export function IndexCardsBar({ indexItems = [], selectedSymbol, onSelect, compact = false }) {
  const cards = useMemo(() => {
    const lookup = new Map(indexItems.map(item => [String(item.symbol || '').toUpperCase(), item]))
    return INDEX_GROUPS.map(group => {
      const live = group.symbols.map(symbol => lookup.get(symbol)).find(Boolean)
      const symbol = live?.symbol || (group.label === 'HNX' ? 'HNXINDEX' : group.symbols[0])
      return { ...live, symbol, label: symbol === 'HNX30' || symbol === 'HNXINDEX30' ? 'HNX30' : group.label }
    })
  }, [indexItems])
  return <section className={`sonar-cards-bar-wrap${compact ? ' is-compact' : ''}`} aria-label="Bảng tổng quan chỉ số">
    <div className="sonar-cards-grid">{cards.map(item => <IndexSparklineCard key={item.symbol} item={item} isSelected={selectedSymbol === item.symbol} onSelect={onSelect} compact={compact}/>)}</div>
  </section>
}
