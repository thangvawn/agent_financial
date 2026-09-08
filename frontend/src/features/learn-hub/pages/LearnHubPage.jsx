import React from 'react'
import LearningHomePage from './LearningHomePage'
import { AgentRunPanel } from '../../../shared/agentic/AgentRunPanel'

export default function LearnHubPage({
  runId,
  status,
  onCancel,
  onArtifactClick,
  sessionId,
  onBack,
}) {
  return (
    <div className="learn-hub-page">
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
      <LearningHomePage sessionId={sessionId} onBack={onBack} />
    </div>
  )
}
