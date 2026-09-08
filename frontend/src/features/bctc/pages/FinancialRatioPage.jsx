import React from 'react'
import BctcAnalysisWorkspace from './BctcAnalysisWorkspace'
import { AgentRunPanel } from '../../../shared/agentic/AgentRunPanel'

export default function FinancialRatioPage({
  runId,
  status,
  onCancel,
  onArtifactClick,
  initialTicker = 'HPG',
  onBack,
  ...props
}) {
  return (
    <div className="financial-ratio-page">
      {runId && (
        <div style={{ padding: '1rem', borderBottom: '1px solid #2a2e39' }}>
          <AgentRunPanel
            runId={runId}
            status={status}
            onCancel={onCancel}
            onArtifactClick={onArtifactClick}
          />
        </div>
      )}
      <BctcAnalysisWorkspace
        initialTicker={initialTicker}
        onBack={onBack}
        {...props}
      />
    </div>
  )
}
