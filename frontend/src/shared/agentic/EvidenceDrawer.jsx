import React, { useEffect, useRef } from "react";

/**
 * Shared EvidenceDrawer: Displays verified evidence rows and provenance citations
 * Surface-agnostic, usable by any agentic workflow (BCTC, Quant, Macro).
 */
export function EvidenceDrawer({
  isOpen,
  onClose,
  artifact,
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

  if (!isOpen || !artifact) {
    return null;
  }

  const isDraft = artifact.review_status === "draft";
  const hasClaims = artifact.claims && artifact.claims.length > 0;
  const hasSourceRefs = artifact.source_refs && artifact.source_refs.length > 0;

  return (
    <aside
      ref={drawerRef}
      role="complementary"
      aria-label="Evidence Source Drawer"
      tabIndex={-1}
      className="agentic-evidence-drawer"
      style={{
        position: "fixed", right: 0, top: 0, bottom: 0, width: "420px",
        backgroundColor: "#ffffff",
        boxShadow: "-4px 0 16px rgba(0,0,0,0.15)",
        zIndex: 1000, display: "flex", flexDirection: "column", outline: "none",
      }}
    >
      <header
        style={{
          padding: "1rem", borderBottom: "1px solid #e5e7eb",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 600 }}>
          Evidence & Citations
        </h3>
        <button
          onClick={onClose}
          aria-label="Close drawer"
          style={{
            background: "none", border: "none", fontSize: "1.25rem",
            cursor: "pointer", padding: "0.25rem 0.5rem",
          }}
        >
          ✕
        </button>
      </header>

      {isDraft && (
        <div
          role="alert"
          aria-live="polite"
          style={{
            backgroundColor: "#fef3c7", color: "#92400e", padding: "0.75rem 1rem",
            fontSize: "0.875rem", borderBottom: "1px solid #fde68a",
          }}
        >
          ⚠️ <strong>Draft Artifact:</strong> This artifact is still under review.
        </div>
      )}

      <div style={{ padding: "1rem", overflowY: "auto", flex: 1 }}>
        <div style={{ marginBottom: "1.25rem" }}>
          <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.95rem" }}>
            Domain: {artifact.domain} | Type: {artifact.artifact_type}
          </h4>
          <span
            style={{
              display: "inline-block", padding: "0.2rem 0.5rem", borderRadius: "4px",
              fontSize: "0.75rem", fontWeight: 500,
              backgroundColor: artifact.review_status === "verified" ? "#d1fae5" : "#f3f4f6",
              color: artifact.review_status === "verified" ? "#065f46" : "#4b5563",
            }}
          >
            Status: {artifact.review_status} (v{artifact.version})
          </span>
        </div>

        {hasSourceRefs && (
          <section style={{ marginBottom: "1.5rem" }}>
            <h5 style={{ margin: "0 0 0.5rem 0", color: "#4b5563" }}>Sources ({artifact.source_refs.length})</h5>
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {artifact.source_refs.map((ref, idx) => (
                <li
                  key={idx}
                  style={{
                    padding: "0.5rem", marginBottom: "0.25rem", backgroundColor: "#f9fafb",
                    borderRadius: "4px", border: "1px solid #e5e7eb", fontSize: "0.85rem",
                  }}
                >
                  <strong>{ref.kind}</strong>: {ref.resource_id} <em>({ref.module})</em>
                </li>
              ))}
            </ul>
          </section>
        )}

        {hasClaims && (
          <section style={{ marginBottom: "1.5rem" }}>
            <h5 style={{ margin: "0 0 0.5rem 0", color: "#4b5563" }}>Verified Claims ({artifact.claims.length})</h5>
            <ul style={{ paddingLeft: "1.25rem", margin: 0, fontSize: "0.85rem" }}>
              {artifact.claims.map((claim, idx) => (
                <li key={idx} style={{ marginBottom: "0.35rem" }}>{claim}</li>
              ))}
            </ul>
          </section>
        )}
        
        {artifact.limitations && artifact.limitations.length > 0 && (
          <section>
            <h5 style={{ margin: "0 0 0.5rem 0", color: "#4b5563" }}>Limitations</h5>
            <ul style={{ paddingLeft: "1.25rem", margin: 0, fontSize: "0.85rem", color: "#9ca3af" }}>
              {artifact.limitations.map((limit, idx) => (
                <li key={idx} style={{ marginBottom: "0.35rem" }}>{limit}</li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </aside>
  );
}
