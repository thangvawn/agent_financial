import React, { useMemo } from 'react';
import {
  extractQuantaParams,
  updateQuantaParamInCode,
} from '../../utils/quantaParamParser';

export default function QuantaParamSliders({ code, onChangeCode, onReset }) {
  const schema = useMemo(() => extractQuantaParams(code), [code]);

  if (schema.length === 0) {
    return (
      <div className="quanta-param-sliders empty">
        <div className="sliders-header">
          <span className="sliders-title">⚡ Tham số động (Dynamic Sliders)</span>
        </div>
        <p className="sliders-empty-msg">
          Chưa tìm thấy tham số trong khối <code>params:</code>. Cú pháp: <code>fast_len = 20 in [5..100]</code>
        </p>
      </div>
    );
  }

  const handleSliderChange = (name, val) => {
    if (onChangeCode) {
      const updated = updateQuantaParamInCode(code, name, val);
      onChangeCode(updated);
    }
  };

  return (
    <div className="quanta-param-sliders">
      <div className="sliders-header">
        <div className="sliders-title">
          <span>⚡ Tham số động (Dynamic Sliders)</span>
          <span className="sliders-badge">{schema.length} params</span>
        </div>
        {onReset && (
          <button type="button" onClick={onReset} className="reset-code-btn">
            Reset
          </button>
        )}
      </div>

      <div className="sliders-grid">
        {schema.map((p) => {
          const step = p.unit === 'pct' ? 0.5 : 1;
          return (
            <div key={p.name} className="slider-item">
              <div className="slider-label-row">
                <span className="slider-param-name">{p.name}</span>
                <span className="slider-param-val">
                  {p.value} {p.unit === 'pct' ? '%' : p.unit}
                </span>
              </div>
              <div className="slider-control-row">
                <span className="slider-bound">{p.min}</span>
                <input
                  type="range"
                  min={p.min}
                  max={p.max}
                  step={step}
                  value={p.value}
                  onChange={(e) => handleSliderChange(p.name, parseFloat(e.target.value))}
                  className="slider-input"
                />
                <span className="slider-bound">{p.max}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
