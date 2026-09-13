import React, { useState } from 'react'
import { AlertTriangle, CheckCircle, Clock, ShieldAlert, X, Play, RefreshCw, FileCheck } from 'lucide-react'
import { executeRun } from '../services/simulationAgentApi'

export default function ActionProposalModal({
  proposal,
  confirmationToken,
  isOpen,
  onClose,
  onConfirmed,
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [receipt, setReceipt] = useState(null)

  if (!isOpen || !proposal) {
    return null
  }

  const manifest = proposal.manifest || {}
  const warnings = manifest.warnings || []

  async function handleConfirm() {
    try {
      setLoading(true)
      setError(null)
      const idempotencyKey = typeof crypto !== 'undefined' && crypto.randomUUID
        ? `idem_${crypto.randomUUID().slice(0, 12)}`
        : `idem_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

      const resReceipt = await executeRun({
        proposal_id: proposal.proposal_id,
        confirmation_token: confirmationToken,
        idempotency_key: idempotencyKey,
      })

      setReceipt(resReceipt)
      if (onConfirmed) {
        onConfirmed(resReceipt)
      }
    } catch (err) {
      setError(err.message || 'Lỗi khi xác nhận thực thi mô phỏng.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="proposal-modal-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1rem',
      }}
    >
      <div
        style={{
          backgroundColor: '#18181b',
          border: '1px solid #27272a',
          borderRadius: '0.75rem',
          maxWidth: '36rem',
          width: '100%',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          color: '#f4f4f5',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #27272a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ShieldAlert size={22} color="#f59e0b" />
            <h2 id="proposal-modal-title" style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0 }}>
              Xác nhận Thực thi Mô phỏng (2-Phase Commit)
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng modal"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#a1a1aa',
              cursor: 'pointer',
              padding: '0.25rem',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {receipt ? (
            /* Success State */
            <div
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid #10b981',
                borderRadius: '0.5rem',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981' }}>
                <CheckCircle size={22} />
                <strong style={{ fontSize: '1rem' }}>Thực thi thành công!</strong>
              </div>
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#d1d5db' }}>
                Simulation Run đã được kích hoạt thành công với chứng từ bất biến:
              </p>
              <div style={{ fontSize: '0.8125rem', color: '#9ca3af', fontFamily: 'monospace' }}>
                <div>Receipt ID: {receipt.receipt_id}</div>
                <div>Proposal ID: {receipt.proposal_id}</div>
                <div>Trạng thái: {receipt.status}</div>
                <div>Artifact ID: {receipt.run_artifact_id || 'N/A'}</div>
                <div>Thời gian: {receipt.executed_at}</div>
              </div>
            </div>
          ) : (
            /* Proposal Details Preview */
            <>
              <div
                style={{
                  backgroundColor: '#27272a',
                  borderRadius: '0.5rem',
                  padding: '1rem',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '0.75rem',
                  fontSize: '0.875rem',
                }}
              >
                <div>
                  <span style={{ color: '#a1a1aa' }}>Chiến lược: </span>
                  <strong>{manifest.strategy_id || 'Chưa đặt tên'}</strong>
                </div>
                <div>
                  <span style={{ color: '#a1a1aa' }}>Phiên bản: </span>
                  <strong>{manifest.strategy_version || '1.0.0'}</strong>
                </div>
                <div>
                  <span style={{ color: '#a1a1aa' }}>Khoảng thời gian: </span>
                  <strong>{manifest.data_start} → {manifest.data_end}</strong>
                </div>
                <div>
                  <span style={{ color: '#a1a1aa' }}>Nguồn dữ liệu: </span>
                  <strong>{manifest.dataset_source} ({manifest.dataset_version})</strong>
                </div>
                <div>
                  <span style={{ color: '#a1a1aa' }}>Phí hoa hồng: </span>
                  <strong>{manifest.commission_pct}%</strong>
                </div>
                <div>
                  <span style={{ color: '#a1a1aa' }}>Trượt giá: </span>
                  <strong>{manifest.slippage_pct}%</strong>
                </div>
                <div>
                  <span style={{ color: '#a1a1aa' }}>Benchmark: </span>
                  <strong>{manifest.benchmark || 'VNINDEX'}</strong>
                </div>
                <div>
                  <span style={{ color: '#a1a1aa' }}>Chi phí ước tính: </span>
                  <strong style={{ color: '#10b981' }}>${proposal.estimated_cost?.toFixed(2) || '0.02'}</strong>
                </div>
              </div>

              {/* Expiry Badge */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.8125rem',
                  color: '#fbbf24',
                }}
              >
                <Clock size={16} />
                <span>Proposal hết hạn lúc: {new Date(proposal.expires_at).toLocaleTimeString()}</span>
              </div>

              {/* Warnings */}
              {warnings.length > 0 && (
                <div
                  style={{
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '0.5rem',
                    padding: '0.75rem 1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                    fontSize: '0.8125rem',
                    color: '#fef3c7',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b' }}>
                    <AlertTriangle size={16} />
                    <strong>Cảnh báo phương pháp luận:</strong>
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                    {warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid #ef4444',
                    borderRadius: '0.5rem',
                    padding: '0.75rem 1rem',
                    color: '#fca5a5',
                    fontSize: '0.875rem',
                  }}
                >
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid #27272a',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            backgroundColor: '#1f1f23',
          }}
        >
          {receipt ? (
            <button
              onClick={onClose}
              style={{
                backgroundColor: '#10b981',
                color: '#fff',
                border: 'none',
                borderRadius: '0.375rem',
                padding: '0.5rem 1.25rem',
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <FileCheck size={16} />
              Hoàn tất
            </button>
          ) : (
            <>
              <button
                onClick={onClose}
                disabled={loading}
                style={{
                  backgroundColor: 'transparent',
                  color: '#a1a1aa',
                  border: '1px solid #3f3f46',
                  borderRadius: '0.375rem',
                  padding: '0.5rem 1rem',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1,
                }}
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleConfirm}
                disabled={loading}
                style={{
                  backgroundColor: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '0.375rem',
                  padding: '0.5rem 1.25rem',
                  fontWeight: 500,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  opacity: loading ? 0.8 : 1,
                }}
              >
                {loading ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Đang thực thi...
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Xác nhận thực thi
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
