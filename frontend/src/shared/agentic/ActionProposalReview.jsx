import React, { useState, useEffect } from 'react';

export function ActionProposalReview({ proposal, onConfirm, onReject }) {
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    if (!proposal?.expires_at) return;
    
    const interval = setInterval(() => {
      const now = new Date();
      const expires = new Date(proposal.expires_at);
      const diff = expires - now;
      
      if (diff <= 0) {
        setTimeLeft('Expired');
        clearInterval(interval);
      } else {
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        setTimeLeft(`${minutes}m ${seconds}s`);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [proposal?.expires_at]);

  if (!proposal) return null;

  const getRiskColor = (risk) => {
    switch(risk?.toLowerCase()) {
      case 'high': return { bg: '#fee2e2', text: '#991b1b' };
      case 'medium': return { bg: '#fef3c7', text: '#92400e' };
      default: return { bg: '#d1fae5', text: '#065f46' };
    }
  };
  
  const riskColor = getRiskColor(proposal.risk_class);

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem', backgroundColor: '#fff', maxWidth: '450px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <h4 style={{ margin: '0 0 0.25rem 0' }}>Action Proposal: {proposal.operation}</h4>
          <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
            Target: {proposal.target?.kind} ({proposal.target?.resource_id})
          </div>
        </div>
        <span style={{ 
          fontSize: '0.75rem', fontWeight: 600, padding: '2px 6px', 
          borderRadius: '4px', backgroundColor: riskColor.bg, color: riskColor.text 
        }}>
          {proposal.risk_class} RISK
        </span>
      </div>

      <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#f3f4f6', borderRadius: '6px', fontSize: '0.85rem', fontFamily: 'monospace', overflowX: 'auto' }}>
        <pre style={{ margin: 0 }}>{JSON.stringify(proposal.payload_preview, null, 2)}</pre>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '0.8rem', color: timeLeft === 'Expired' ? '#ef4444' : '#6b7280' }}>
          {timeLeft === 'Expired' ? 'Proposal expired' : `Expires in: ${timeLeft}`}
        </div>
        
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            onClick={onReject}
            style={{ padding: '0.5rem 1rem', borderRadius: '4px', border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', fontSize: '0.875rem' }}
          >
            Reject
          </button>
          <button 
            onClick={onConfirm}
            disabled={timeLeft === 'Expired'}
            style={{ padding: '0.5rem 1rem', borderRadius: '4px', border: 'none', background: timeLeft === 'Expired' ? '#9ca3af' : '#2563eb', color: '#fff', cursor: timeLeft === 'Expired' ? 'not-allowed' : 'pointer', fontSize: '0.875rem', fontWeight: 500 }}
          >
            Confirm Action
          </button>
        </div>
      </div>
    </div>
  );
}
