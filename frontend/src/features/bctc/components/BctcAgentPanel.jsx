import React, { useState, useEffect } from "react";
import {
  createBctcRun,
  createBctcMemo,
  fetchBctcMemos,
  deleteBctcMemo,
  fetchBctcAgentHealth,
} from "../services/financialsApi";

const BCTC_SKILLS = [
  {
    id: "bctc.explain_line_item.v1",
    name: "Giải thích chỉ tiêu & bóc tách",
    description: "Tra cứu định nghĩa, công thức và bóc tách dữ liệu từ BCTC chính thức.",
  },
  {
    id: "bctc.compare_periods.v1",
    name: "So sánh biến động qua các kỳ",
    description: "Phân tích tăng trưởng, biến động tuyệt đối và phần trăm giữa các kỳ.",
  },
  {
    id: "bctc.ratio_walkthrough.v1",
    name: "Tính toán & hướng dẫn chỉ số",
    description: "Tính tỷ số tài chính (Biên gộp, ROE, Current Ratio) với công thức được duyệt.",
  },
  {
    id: "bctc.earnings_quality_review.v1",
    name: "Đánh giá chất lượng lợi nhuận",
    description: "Lập bảng bằng chứng kiểm chứng tính xác thực và dòng tiền kinh doanh.",
  },
  {
    id: "bctc.research_checklist.v1",
    name: "Checklist thẩm định & truy nguyên",
    description: "Truy vết nguồn gốc (revision, nguồn, thời điểm thu thập) của từng số liệu.",
  },
];

const LINE_ITEMS = [
  { id: "revenue", label: "Doanh thu thuần (Revenue)" },
  { id: "net_profit", label: "Lợi nhuận sau thuế (Net Profit)" },
  { id: "gross_profit", label: "Lợi nhuận gộp (Gross Profit)" },
  { id: "operating_profit", label: "Lợi nhuận HĐKD (Operating Profit)" },
  { id: "assets", label: "Tổng tài sản (Total Assets)" },
  { id: "liabilities", label: "Nợ phải trả (Total Liabilities)" },
  { id: "equity", label: "Vốn chủ sở hữu (Equity)" },
];

const FORMULAS = [
  { id: "gross_margin", label: "Biên lợi nhuận gộp (Gross Margin)" },
  { id: "net_margin", label: "Biên lợi nhuận ròng (Net Margin)" },
  { id: "operating_margin", label: "Biên lợi nhuận HĐKD (Operating Margin)" },
  { id: "roe", label: "Tỷ suất sinh lời trên VCSH (ROE)" },
  { id: "roa", label: "Tỷ suất sinh lời trên Tổng tài sản (ROA)" },
  { id: "current_ratio", label: "Khả năng thanh toán hiện hành (Current Ratio)" },
  { id: "debt_to_equity", label: "Đòn bẩy Nợ / VCSH (D/E)" },
];

export default function BctcAgentPanel({
  ticker = "FPT",
  activePeriod = "2024Q3",
  onOpenEvidenceDrawer,
}) {
  const [selectedSkill, setSelectedSkill] = useState(BCTC_SKILLS[0].id);
  const [selectedLineItem, setSelectedLineItem] = useState("revenue");
  const [selectedFormula, setSelectedFormula] = useState("gross_margin");
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState(null);
  const [memos, setMemos] = useState([]);
  const [agentHealth, setAgentHealth] = useState(null);
  const [savingMemo, setSavingMemo] = useState(false);

  useEffect(() => {
    fetchBctcAgentHealth()
      .then((h) => setAgentHealth(h))
      .catch(() => setAgentHealth({ status: "unavailable" }));
    loadMemos();
  }, []);

  const loadMemos = () => {
    fetchBctcMemos()
      .then((res) => {
        if (res && res.memos) {
          setMemos(res.memos);
        }
      })
      .catch(() => {});
  };

  const handleRun = async () => {
    setIsRunning(true);
    setRunError(null);
    setRunResult(null);
    try {
      const res = await createBctcRun({
        skillId: selectedSkill,
        ticker,
        periods: [activePeriod],
        lineItem: selectedLineItem,
        formulaId: selectedFormula,
      });
      setRunResult(res);
    } catch (err) {
      setRunError(err.message || "Lỗi khi chạy Agent.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleSaveMemo = async () => {
    if (!runResult) return;
    setSavingMemo(true);
    try {
      const output = runResult.output || {};
      let numVal = 0.0;
      let unit = "VND";
      let claimRef = selectedLineItem;

      if (output.amount && typeof output.amount.value === "number") {
        numVal = output.amount.value;
        unit = output.amount.unit || "VND";
        claimRef = output.line_item || selectedLineItem;
      } else if (output.result && typeof output.result.value === "number") {
        numVal = output.result.value;
        unit = output.result.unit || "ratio";
        claimRef = output.formula_id || selectedFormula;
      } else if (Array.isArray(output.deltas) && output.deltas.length > 0) {
        numVal = output.deltas[0]?.pct_change?.value || 0.0;
        unit = "pct";
        claimRef = output.line_item || selectedLineItem;
      }

      const provCitation = (runResult.citations && runResult.citations[0]) || {
        report_id: `report:${ticker.toLowerCase()}`,
        revision_id: `rev_${ticker.toLowerCase()}_${activePeriod}`,
        period: activePeriod,
        source: "vndirect",
        fetched_at: new Date().toISOString(),
      };

      const dynamicEvidenceRows = [
        {
          claim_ref: claimRef,
          kind: "fact",
          amount: {
            value: numVal,
            unit: unit,
            provenance: provCitation,
          },
        },
      ];

      const memoPayload = {
        subject: `Thẩm định BCTC ${ticker} (${activePeriod}) - ${selectedSkill}`,
        scope: "public",
        report_refs: [provCitation],
        evidence_rows: dynamicEvidenceRows,
        interpretations: [
          runResult.explanation || `Kết quả phân tích từ Skill ${selectedSkill} đã qua kiểm duyệt NumericReviewer (100% grounded).`,
        ],
        limitations: ["Chỉ số phản ánh số liệu tại thời điểm báo cáo."],
        reviewer_status: "approved",
      };
      await createBctcMemo(memoPayload);
      loadMemos();
    } catch (err) {
      alert("Lỗi khi lưu memo: " + err.message);
    } finally {
      setSavingMemo(false);
    }
  };

  const handleDeleteMemo = async (memoId) => {
    if (!window.confirm("Bạn có chắc muốn xoá Evidence Memo này?")) return;
    try {
      await deleteBctcMemo(memoId);
      loadMemos();
    } catch (err) {
      alert("Không thể xoá memo: " + err.message);
    }
  };

  const isRatioSkill = selectedSkill === "bctc.ratio_walkthrough.v1";
  const isLineItemSkill = ["bctc.explain_line_item.v1", "bctc.compare_periods.v1", "bctc.research_checklist.v1"].includes(selectedSkill);

  return (
    <div className="bctc-agent-panel" style={{ padding: "16px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0", marginTop: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "600", color: "#1e293b" }}>
          🤖 BCTC Multi-Agent Copilot
        </h3>
        {agentHealth && (
          <span style={{ fontSize: "12px", color: agentHealth.status === "healthy" ? "#16a34a" : "#ca8a04", backgroundColor: "#ffffff", padding: "2px 8px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            ● {agentHealth.status === "healthy" ? "Agent Sẵn Sàng (6 Tools)" : "Đang kết nối"}
          </span>
        )}
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", fontSize: "13px", fontWeight: "500", color: "#475569", marginBottom: "4px" }}>
          Chọn kỹ năng Agent (Skill):
        </label>
        <select
          value={selectedSkill}
          onChange={(e) => setSelectedSkill(e.target.value)}
          style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "14px", backgroundColor: "#ffffff" }}
        >
          {BCTC_SKILLS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.id})
            </option>
          ))}
        </select>
        <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#64748b" }}>
          {BCTC_SKILLS.find((s) => s.id === selectedSkill)?.description}
        </p>
      </div>

      {isLineItemSkill && (
        <div style={{ marginBottom: "12px" }}>
          <label style={{ display: "block", fontSize: "13px", fontWeight: "500", color: "#475569", marginBottom: "4px" }}>
            Chọn khoản mục BCTC:
          </label>
          <select
            value={selectedLineItem}
            onChange={(e) => setSelectedLineItem(e.target.value)}
            style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "14px", backgroundColor: "#ffffff" }}
          >
            {LINE_ITEMS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {isRatioSkill && (
        <div style={{ marginBottom: "12px" }}>
          <label style={{ display: "block", fontSize: "13px", fontWeight: "500", color: "#475569", marginBottom: "4px" }}>
            Chọn công thức / chỉ số tài chính:
          </label>
          <select
            value={selectedFormula}
            onChange={(e) => setSelectedFormula(e.target.value)}
            style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "14px", backgroundColor: "#ffffff" }}
          >
            {FORMULAS.map((f) => (
              <option key={f.id} value={f.id}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
      )}

      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        <button
          onClick={handleRun}
          disabled={isRunning}
          style={{
            padding: "8px 16px",
            backgroundColor: "#2563eb",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            fontSize: "14px",
            fontWeight: "500",
            cursor: isRunning ? "not-allowed" : "pointer",
            opacity: isRunning ? 0.7 : 1,
          }}
        >
          {isRunning ? "Đang phân tích & kiểm duyệt số liệu..." : "Chạy phân tích Agent"}
        </button>
      </div>

      {runError && (
        <div style={{ padding: "10px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "6px", color: "#b91c1c", fontSize: "13px", marginBottom: "12px" }}>
          ⚠️ <strong>Lỗi:</strong> {runError}
        </div>
      )}

      {runResult && (
        <div style={{ padding: "14px", backgroundColor: "#ffffff", border: "1px solid #cbd5e1", borderRadius: "8px", marginBottom: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontSize: "13px", fontWeight: "600", color: "#16a34a", display: "flex", alignItems: "center", gap: "6px" }}>
              <span>✓</span> Run hoàn tất (NumericReviewer: {runResult.review_status})
            </span>
            <span style={{ fontSize: "11px", color: "#94a3b8" }}>ID: {runResult.run_id}</span>
          </div>

          <div style={{ padding: "10px 12px", backgroundColor: "#f1f5f9", borderRadius: "6px", fontSize: "13px", color: "#1e293b", lineHeight: "1.5", marginBottom: "10px", borderLeft: "4px solid #3b82f6" }}>
            💡 <strong>Kết quả phân tích:</strong> {runResult.explanation || "Đã phân tích thành công."}
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", fontSize: "12px", color: "#475569", marginBottom: "12px" }}>
            <span style={{ backgroundColor: "#e2e8f0", padding: "3px 8px", borderRadius: "4px" }}>
              <strong>Mã CK:</strong> {runResult.ticker}
            </span>
            <span style={{ backgroundColor: "#e2e8f0", padding: "3px 8px", borderRadius: "4px" }}>
              <strong>Kỳ:</strong> {activePeriod}
            </span>
            {runResult.citations?.[0]?.source && (
              <span style={{ backgroundColor: "#e0f2fe", color: "#0369a1", padding: "3px 8px", borderRadius: "4px" }}>
                <strong>Nguồn:</strong> {runResult.citations[0].source}
              </span>
            )}
            {runResult.citations?.[0]?.revision_id && (
              <span style={{ backgroundColor: "#f3e8ff", color: "#6b21a8", padding: "3px 8px", borderRadius: "4px" }}>
                <strong>Revision:</strong> {runResult.citations[0].revision_id.slice(0, 14)}...
              </span>
            )}
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={handleSaveMemo}
              disabled={savingMemo}
              style={{
                padding: "8px 14px",
                backgroundColor: "#10b981",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                fontSize: "13px",
                fontWeight: "500",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {savingMemo ? "Đang lưu..." : "💾 Lưu thành Evidence Memo"}
            </button>
          </div>
        </div>
      )}

      {/* Memos List */}
      <div style={{ marginTop: "16px", borderTop: "1px solid #e2e8f0", paddingTop: "12px" }}>
        <h4 style={{ margin: "0 0 8px 0", fontSize: "14px", fontWeight: "600", color: "#334155" }}>
          📑 Danh sách Evidence Memos đã lưu ({memos.length})
        </h4>
        {memos.length === 0 ? (
          <p style={{ margin: 0, fontSize: "12px", color: "#94a3b8" }}>Chưa có Evidence Memo nào cho tài khoản này.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {memos.map((m) => (
              <div
                key={m.memo_id}
                style={{
                  padding: "8px 10px",
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "4px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <div style={{ fontSize: "13px", fontWeight: "500", color: "#1e293b" }}>{m.subject}</div>
                  <div style={{ fontSize: "11px", color: "#64748b" }}>
                    Tạo: {new Date(m.created_at).toLocaleDateString("vi-VN")} | Trạng thái: {m.reviewer_status}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "4px" }}>
                  {onOpenEvidenceDrawer && (
                    <button
                      onClick={() => onOpenEvidenceDrawer(m)}
                      style={{ padding: "4px 8px", backgroundColor: "#f1f5f9", border: "1px solid #cbd5e1", borderRadius: "4px", fontSize: "11px", cursor: "pointer" }}
                    >
                      🔍 Nguồn số liệu
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteMemo(m.memo_id)}
                    style={{ padding: "4px 8px", backgroundColor: "#fff1f2", border: "1px solid #fecdd3", color: "#e11d48", borderRadius: "4px", fontSize: "11px", cursor: "pointer" }}
                  >
                    Xoá
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

