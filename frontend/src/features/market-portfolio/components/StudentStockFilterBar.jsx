import React from 'react'
import { PRESET_PACKS, VN_SECTORS_31, EXCHANGES, TECHNICAL_FILTERS } from '../services/filterPresetData'

export function StudentStockFilterBar({
  activePreset = '',
  onSelectPreset,
  selectedSector = '',
  onSelectSector,
  selectedExchange = '',
  onSelectExchange,
  selectedTechnical = 'all',
  onSelectTechnical,
  matchCount = 0,
  onReset
}) {
  const isFiltered = Boolean(activePreset || selectedSector || selectedExchange || (selectedTechnical && selectedTechnical !== 'all'))

  return (
    <div className="student-filter-bar">
      <div className="student-filter-header">
        <div className="filter-title-group">
          <span className="filter-badge">Bộ Lọc Sinh Viên</span>
          <span className="filter-subtitle">Phân loại tín hiệu & cơ hội thị trường</span>
        </div>
        <div className="filter-actions-group">
          <span className="match-count-badge">
            Tìm thấy <strong>{matchCount}</strong> mã
          </span>
          {isFiltered && (
            <button type="button" className="btn-reset-filter" onClick={onReset} title="Xóa toàn bộ tiêu chí lọc">
              Đặt lại
            </button>
          )}
        </div>
      </div>

      <div className="preset-packs-scroll" role="tablist" aria-label="1-Click Preset Packs">
        {PRESET_PACKS.map((pack) => {
          const isActive = activePreset === pack.id
          return (
            <button
              type="button"
              key={pack.id}
              role="tab"
              aria-selected={isActive}
              className={`preset-pack-chip group-${pack.group} ${isActive ? 'is-active' : ''}`}
              onClick={() => onSelectPreset?.(isActive ? '' : pack.id)}
              title={pack.desc}
            >
              <span className="pack-label">{pack.label}</span>
            </button>
          )
        })}
      </div>

      <div className="filter-dropdowns-row">
        <div className="dropdown-control">
          <label htmlFor="filter-exchange">Sàn:</label>
          <select
            id="filter-exchange"
            value={selectedExchange}
            onChange={(e) => onSelectExchange?.(e.target.value)}
            className="select-custom"
          >
            {EXCHANGES.map((ex) => (
              <option key={ex.id} value={ex.id}>{ex.label}</option>
            ))}
          </select>
        </div>

        <div className="dropdown-control">
          <label htmlFor="filter-sector">Nhóm ngành (31 ngành):</label>
          <select
            id="filter-sector"
            value={selectedSector}
            onChange={(e) => onSelectSector?.(e.target.value)}
            className="select-custom"
          >
            <option value="">Tất cả 31 nhóm ngành</option>
            {VN_SECTORS_31.map((sec) => (
              <option key={sec.id} value={sec.name}>{sec.name}</option>
            ))}
          </select>
        </div>

        <div className="dropdown-control">
          <label htmlFor="filter-tech">Chỉ báo Kỹ thuật:</label>
          <select
            id="filter-tech"
            value={selectedTechnical}
            onChange={(e) => onSelectTechnical?.(e.target.value)}
            className="select-custom"
          >
            {TECHNICAL_FILTERS.map((tech) => (
              <option key={tech.id} value={tech.id}>{tech.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
