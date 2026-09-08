import React, { useEffect } from 'react';
import { useAgentRun } from './useAgentRun';
import { AgentArtifactCard } from './AgentArtifactCard';

export function AgentRunPanel({
  runId,
  status: statusProp,
  onCancel,
  onArtifactClick,
  onComplete,
  onError,
}) {
  const hookResult = useAgentRun(runId);
  const status = statusProp || hookResult.status;
  const artifact = hookResult.artifact;
  const error = hookResult.error;
  const cancel = onCancel || hookResult.cancel;
  const isLoading = statusProp ? false : hookResult.isLoading;

  useEffect(() => {
    if (status === 'completed' || status === 'degraded') {
      onComplete?.(artifact);
    } else if (status === 'failed' || error) {
      onError?.(error || new Error('Run failed'));
    }
  }, [status, artifact, error, onComplete, onError]);

  if (!runId) return null;

  const isActive = ['running', 'reviewing', 'awaiting_confirmation'].includes(status);
  
  return (
    <div className="agent-run-panel" style={{ padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, fontSize: '1rem' }}>
          Agentic Task
          <span style={{ marginLeft: '8px', fontSize: '0.8rem', color: '#6b7280', fontWeight: 'normal' }}>
            ID: {runId.substring(0, 12)}...
          </span>
        </h3>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ 
            fontSize: '0.8rem', fontWeight: 500, padding: '2px 8px', borderRadius: '99px',
            backgroundColor: status === 'completed' ? '#d1fae5' : status === 'failed' ? '#fee2e2' : '#e0e7ff',
            color: status === 'completed' ? '#065f46' : status === 'failed' ? '#991b1b' : '#3730a3'
          }}>
            {isLoading ? 'loading...' : status.toUpperCase()}
          </span>
          
          {isActive && (
            <button 
              onClick={cancel}
              style={{ background: 'none', border: '1px solid #d1d5db', borderRadius: '4px', padding: '0.25rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer' }}
            >
              Cancel
            </button>
          )}
        </div>
      </header>

      {error && (
        <div style={{ color: '#b91c1c', fontSize: '0.875rem', padding: '0.5rem', backgroundColor: '#fef2f2', borderRadius: '4px', marginBottom: '1rem' }}>
          Error: {error.message || 'Failed to fetch run status'}
        </div>
      )}

      {isActive && (
        <div style={{ padding: '1rem', display: 'flex', justifyContent: 'center', color: '#6b7280' }}>
          <div className="spinner" style={{ animation: 'spin 1s linear infinite' }}>↻</div>
          <span style={{ marginLeft: '0.5rem' }}>Agent is working...</span>
        </div>
      )}

      {artifact && (
        <div style={{ marginTop: '1rem' }}>
          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: '#4b5563' }}>Generated Artifacts</h4>
          <AgentArtifactCard artifact={artifact} onArtifactClick={onArtifactClick} />
        </div>
      )}
    </div>
  );
}
