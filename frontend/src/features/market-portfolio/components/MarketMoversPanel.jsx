import React from 'react'
import { ForeignFlowButterfly } from './ForeignFlowButterfly'
import { VnIndexImpactWidget } from './VnIndexImpactWidget'
import { MarketMomentumWidgets } from './MarketMomentumWidgets'
import { SectorHeatGrid } from './SectorHeatGrid'

export function MarketMoversPanel({ items = [], onSelectSymbol, onSelectSector, activeSector = '' }) {
  return (
    <section className="market-movers-panel" aria-label="Toàn cảnh diễn biến thị trường">
      <div className="movers-row-duo">
        <div className="movers-col">
          <ForeignFlowButterfly items={items} onSelectSymbol={onSelectSymbol} />
        </div>
        <div className="movers-col">
          <VnIndexImpactWidget items={items} onSelectSymbol={onSelectSymbol} />
        </div>
      </div>

      <div className="movers-row-duo">
        <div className="movers-col">
          <MarketMomentumWidgets onSelectSymbol={onSelectSymbol} />
        </div>
        <div className="movers-col">
          <SectorHeatGrid onSelectSector={onSelectSector} activeSector={activeSector} />
        </div>
      </div>
    </section>
  )
}
