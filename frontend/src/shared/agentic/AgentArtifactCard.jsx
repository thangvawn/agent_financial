import React, { useState } from 'react';
import { EvidenceDrawer } from './EvidenceDrawer';

export function AgentArtifactCard({ artifact, onArtifactClick }) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  if (!artifact) return null;

  const handleClick = () => {
    setIsDrawerOpen(true);
    onArtifactClick?.(artifact);
  };

  const claimCount = artifact.claims?.length || 0;
  const sourceCount = artifact.source_refs?.length || 0;
  const limitCount = artifact.limitations?.length || 0;

  return (
    <>
      <div 
        className="agent-artifact-card"
        onClick={handleClick}
        style={{
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '1rem',
          cursor: 'pointer',
          backgroundColor: '#fff',
          transition: 'box-shadow 0.2s',
          maxWidth: '400px'
        }}
        onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}
        onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>{artifact.domain} Result</h4>
          <span style={{ 
            fontSize: '0.75rem', 
            padding: '2px 6px', 
            borderRadius: '9999px', 
            backgroundColor: '#e0e7ff', 
            color: '#3730a3' 
          }}>
            {artifact.artifact_type} v{artifact.version}
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem', color: '#4b5563', marginBottom: '0.75rem' }}>
          <span>✓ {claimCount} claims</span>
          <span>📚 {sourceCount} sources</span>
        </div>
        
        {limitCount > 0 && (
          <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
            ⚠️ {limitCount} limitations applied
          </div>
        )}
      </div>

      <EvidenceDrawer 
        isOpen={isDrawerOpen} 
        onClose={() => setIsDrawerOpen(false)} 
        artifact={artifact} 
      />
    </>
  );
}
