import { useEffect, useRef } from 'react'

/**
 * EvidenceSourceDrawer: Displays verified financial evidence rows and provenance citations.
 * Supports keyboard navigation, focus restore, and screen-reader polite notifications.
 */
export default function EvidenceSourceDrawer({
  isOpen,
  onClose,
  memo,
  currentRevisionId,
}) {
  const drawerRef = useRef(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      drawerRef.current?.focus();
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !memo) {
    return null;
  }

  const isStale =
    memo.is_stale ||
    (currentRevisionId &&
      memo.report_refs?.some((r) => r.revision_id !== currentRevisionId));

  return (
    <aside
      ref={drawerRef}
      role="complementary"
      aria-label="BCTC Evidence Source Drawer"
      tabIndex={-1}
      className="bctc-evidence-drawer"
      style={{
        position: "fixed",
        right: 0,
        top: 0,
        bottom: 0,
        width: "420px",
        backgroundColor: "var(--surface)",
        boxShadow: "-4px 0 16px rgba(0,0,0,0.15)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        outline: "none",
      }}
    >
      <header
        style={{
          padding: "1rem",
          borderBottom: "1px solid var(--line)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 600 }}>
          Nguồn Dữ Liệu & Bằng Chứng
        </h3>
        <button
          onClick={onClose}
          aria-label="Đóng bảng nguồn dữ liệu"
          style={{
            background: "none",
            border: "none",
            fontSize: "1.25rem",
            cursor: "pointer",
            padding: "0.25rem 0.5rem",
          }}
        >
          ✕
        </button>
      </header>

      {isStale && (
        <div
          role="alert"
          aria-live="polite"
          style={{
            backgroundColor: "var(--warn-soft)",
            color: "var(--warn)",
            padding: "0.75rem 1rem",
            fontSize: "0.875rem",
            borderBottom: "1px solid #fde68a",
          }}
        >
          ⚠️ <strong>Dữ liệu cũ (Stale):</strong> Báo cáo tài chính đã có phiên
          bản sửa đổi mới. Hãy làm mới để nhận số liệu mới nhất.
        </div>
      )}

      <div style={{ padding: "1rem", overflowY: "auto", flex: 1 }}>
        <div style={{ marginBottom: "1.25rem" }}>
          <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.95rem" }}>
            Chủ đề: {memo.subject}
          </h4>
          <span
            style={{
              display: "inline-block",
              padding: "0.2rem 0.5rem",
              borderRadius: "4px",
              fontSize: "0.75rem",
              fontWeight: 500,
              backgroundColor:
                memo.reviewer_status === "approved" ? "#d1fae5" : "var(--warn-soft)",
              color:
                memo.reviewer_status === "approved" ? "#065f46" : "var(--warn)",
            }}
          >
            Trạng thái kiểm duyệt: {memo.reviewer_status}
          </span>
        </div>

        <section style={{ marginBottom: "1.5rem" }}>
          <h5 style={{ margin: "0 0 0.5rem 0", color: "var(--ink-muted)" }}>
            Bảng bằng chứng số liệu ({memo.evidence_rows?.length || 0})
          </h5>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {memo.evidence_rows?.map((row, idx) => (
              <li
                key={idx}
                style={{
                  padding: "0.75rem",
                  marginBottom: "0.5rem",
                  backgroundColor: "var(--surface-alt)",
                  borderRadius: "6px",
                  border: "1px solid var(--line)",
                  fontSize: "0.85rem",
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>
                  {row.claim}
                </div>
                <div style={{ color: "var(--ink-muted)", fontSize: "0.75rem" }}>
                  <div>Nguồn: {row.citation?.source}</div>
                  <div>Kỳ: {row.citation?.period} | Rev: {row.citation?.revision_id}</div>
                  <div>Thu thập lúc: {row.citation?.fetched_at}</div>
                </div>
              </li>
            ))}
          </ul>
        </section>

        {memo.interpretations?.length > 0 && (
          <section>
            <h5 style={{ margin: "0 0 0.5rem 0", color: "var(--ink-muted)" }}>
              Nhận định & Diễn giải
            </h5>
            <ul style={{ paddingLeft: "1.25rem", margin: 0, fontSize: "0.85rem" }}>
              {memo.interpretations.map((interp, idx) => (
                <li key={idx} style={{ marginBottom: "0.35rem" }}>
                  {interp}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </aside>
  );
}

