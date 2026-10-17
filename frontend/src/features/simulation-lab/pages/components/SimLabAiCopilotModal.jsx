import React, { useState } from 'react';

const PRESET_PROMPTS = [
  {
    title: 'Tối ưu hóa Sharpe & Giảm Whipsaw',
    desc: 'Tăng chu kỳ lọc nhiễu đường xu hướng và thêm điều kiện khối lượng để tránh tín hiệu giả.',
    patch: `params:
  fast_period: 12
  slow_period: 26
  take_profit_pct: 12.0
  stop_loss_pct: 4.5
  trailing_stop: 3.0
`,
  },
  {
    title: 'Phòng thủ rủi ro T+2 (Thị trường VN)',
    desc: 'Thắt chặt biên độ cắt lỗ xuống 3.5% và chỉ vào lệnh khi thanh khoản phiên sáng vượt 1.5x MA20.',
    patch: `params:
  fast_period: 14
  slow_period: 30
  take_profit_pct: 9.0
  stop_loss_pct: 3.5
  trailing_stop: 2.0
`,
  },
];

export default function SimLabAiCopilotModal({ isOpen, onClose, currentCode, onApplyCode }) {
  const [promptInput, setPromptInput] = useState('');
  const [aiResponse, setAiResponse] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  if (!isOpen) return null;

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
      setAiResponse({
        critique:
          'Chiến lược hiện tại có tỷ lệ thắng khả quan, nhưng cần chú ý rủi ro kẹt hàng T+2 khi thị trường có gap down. Nên nới rộng Take Profit lên 12% để đạt Risk/Reward tối thiểu 1:2.5.',
        suggestion: `params:
  fast_period: 10
  slow_period: 24
  take_profit_pct: 11.5
  stop_loss_pct: 4.0
  trailing_stop: 2.5`,
      });
    }, 600);
  };

  const handleApplyPreset = (patch) => {
    if (onApplyCode) {
      const updatedCode = currentCode.replace(/params:[\s\S]*?(?=\n\w+:|$)/, patch);
      onApplyCode(updatedCode);
      onClose();
    }
  };

  return (
    <div className="simlab-modal-backdrop" onClick={onClose}>
      <div className="simlab-copilot-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="copilot-icon">✦</span>
            <h3>AI Quant Copilot & Chiến Lược Cố Vấn</h3>
          </div>
          <button type="button" className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="copilot-prompt-bar">
            <input
              type="text"
              placeholder="Yêu cầu AI (VD: Tối ưu cho FPT khung D1, thêm điều kiện thanh khoản...)"
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            <button
              type="button"
              className="analyze-btn"
              onClick={handleAnalyze}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? 'Đang phân tích...' : 'Phân tích'}
            </button>
          </div>

          {aiResponse && (
            <div className="copilot-analysis-result">
              <h4>Đánh giá từ AI Quant:</h4>
              <p>{aiResponse.critique}</p>
              <button
                type="button"
                className="apply-suggestion-btn"
                onClick={() => handleApplyPreset(aiResponse.suggestion)}
              >
                Áp dụng tham số khuyến nghị ➔
              </button>
            </div>
          )}

          <div className="copilot-presets-group">
            <h4>Đề xuất kịch bản tối ưu nhanh:</h4>
            <div className="presets-list">
              {PRESET_PROMPTS.map((p, idx) => (
                <div key={idx} className="copilot-preset-card">
                  <div>
                    <h5>{p.title}</h5>
                    <p>{p.desc}</p>
                  </div>
                  <button
                    type="button"
                    className="preset-apply-btn"
                    onClick={() => handleApplyPreset(p.patch)}
                  >
                    Áp dụng
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
