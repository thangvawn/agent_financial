import React, { useMemo } from 'react'
import { VN_SECTORS_31 } from '../services/filterPresetData'

const MOCK_SECTOR_PERF = {
  'Ngân hàng': { changePct: 1.45, turnoverB: 3250.4 },
  'Bất động sản': { changePct: -1.82, turnoverB: 2410.2 },
  'Chứng khoán': { changePct: 2.15, turnoverB: 1890.6 },
  'Thép & Kim loại': { changePct: 0.85, turnoverB: 1420.0 },
  'Bán lẻ': { changePct: 1.95, turnoverB: 850.5 },
  'Dầu khí': { changePct: -0.65, turnoverB: 640.2 },
  'Công nghệ thông tin': { changePct: 2.80, turnoverB: 1120.3 },
  'Hóa chất & Phân bón': { changePct: 3.20, turnoverB: 780.4 },
  'Xây dựng & Vật liệu': { changePct: -0.45, turnoverB: 590.1 },
  'Vận tải & Cảng biển': { changePct: 1.10, turnoverB: 480.0 },
  'Thực phẩm & Đồ uống': { changePct: -0.30, turnoverB: 450.0 },
  'Thủy sản': { changePct: 1.60, turnoverB: 390.5 },
  'Bất động sản KCN': { changePct: 2.40, turnoverB: 520.0 },
  'Điện, Nước & Tiện ích': { changePct: 0.15, turnoverB: 310.2 },
  'Dệt may & Da giày': { changePct: -0.90, turnoverB: 220.0 },
  'Dược phẩm & Y tế': { changePct: 0.40, turnoverB: 180.0 }
}

export function SectorHeatGrid({ onSelectSector, activeSector = '' }) {
  const sortedSectors = useMemo(() => {
    return VN_SECTORS_31.map((sec) => {
      const perf = MOCK_SECTOR_PERF[sec.name] || {
        changePct: Number((((sec.code.charCodeAt(0) % 7) - 3) * 0.45).toFixed(2)),
        turnoverB: Number(((sec.code.charCodeAt(1) % 9 + 1) * 65.5).toFixed(1))
      }
      return { ...sec, ...perf }
    }).sort((a, b) => b.changePct - a.changePct)
  }, [])

  return (
    <div className="sector-heat-card">
      <div className="sector-heat-header">
        <div className="sector-title-wrap">
          <h3 className="heat-title">Bản Đồ Nhiệt 31 Nhóm Ngành (Hiệu Suất Phiên)</h3>
        </div>
        <span className="heat-hint">Nhấp vào ngành để lọc nhanh</span>
      </div>

      <div className="sector-heat-grid">
        {sortedSectors.map((sec) => {
          const isSelected = activeSector === sec.name
          const chg = sec.changePct
          let heatTone = 'heat-flat'
          if (chg >= 2.0) heatTone = 'heat-pos-strong'
          else if (chg > 0) heatTone = 'heat-pos'
          else if (chg <= -2.0) heatTone = 'heat-neg-strong'
          else if (chg < 0) heatTone = 'heat-neg'

          return (
            <div
              key={sec.id}
              className={`sector-tile ${heatTone} ${isSelected ? 'is-selected' : ''}`}
              onClick={() => onSelectSector?.(isSelected ? '' : sec.name)}
              role="button"
              tabIndex={0}
              title={`Ngành ${sec.name}: ${chg >= 0 ? '+' : ''}${chg}% | GTGD: ${sec.turnoverB} Tỷ`}
            >
              <span className="sector-name">{sec.name}</span>
              <div className="sector-stats">
                <span className="sector-pct bold">
                  {chg >= 0 ? '+' : ''}{chg.toFixed(2)}%
                </span>
                <span className="sector-turnover">{sec.turnoverB} Tỷ</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
