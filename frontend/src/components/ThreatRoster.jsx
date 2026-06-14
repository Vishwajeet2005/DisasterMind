import React from 'react';

const RISK = {
  CRITICAL: { color: 'var(--risk-critical-color)', bg: 'var(--risk-critical-bg)' },
  HIGH:     { color: 'var(--risk-high-color)',     bg: 'var(--risk-high-bg)' },
  MODERATE: { color: 'var(--risk-moderate-color)', bg: 'var(--risk-moderate-bg)' },
  LOW:      { color: 'var(--risk-low-color)',      bg: 'var(--risk-low-bg)' },
};

export default function ThreatRoster({ threats, selectedCell, onSelect, loading }) {
  const count = threats?.length || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-header">
        <span className="panel-title">Active Regions</span>
        <span className={`panel-badge ${count > 0 ? 'critical' : ''}`}>{count}</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {loading ? (
          <div style={{ padding: 16, color: 'var(--text-faint)' }}>Loading regions…</div>
        ) : !Array.isArray(threats) || threats.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-faint)' }}>
            No active alerts
          </div>
        ) : (
          threats.map((threat) => {
            const rs = RISK[threat.risk_level] || RISK.MODERATE;
            const isSelected = selectedCell?.cell_id === threat.cell_id;
            
            return (
              <div
                key={threat.cell_id}
                onClick={() => onSelect && onSelect(threat)}
                className="fade-in"
                style={{
                  padding: '12px 16px',
                  borderBottom: 'var(--border-subtle)',
                  background: isSelected ? 'var(--bg-card)' : 'transparent',
                  borderLeft: `2px solid ${isSelected ? rs.color : 'transparent'}`,
                  cursor: 'pointer',
                  transition: 'background 0.1s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {threat.cell_name}
                  </span>
                  <span style={{
                    fontSize: 10, fontWeight: 600,
                    color: rs.color, background: rs.bg,
                    padding: '2px 6px', borderRadius: 'var(--radius-sm)'
                  }}>
                    {threat.risk_level}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  {threat.state}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
