import React, { useEffect, useRef } from 'react';

const SEV = {
  CRITICAL: { color: 'var(--risk-critical-color)', label: 'Critical' },
  HIGH:     { color: 'var(--risk-high-color)',     label: 'High' },
  ALERT:    { color: 'var(--risk-critical-color)', label: 'Alert' },
  ERROR:    { color: 'var(--risk-critical-color)', label: 'Error' },
  WARNING:  { color: 'var(--risk-high-color)',     label: 'Warning' },
  INFO:     { color: 'var(--text-secondary)',      label: 'Info' },
};

export default function AgentFeed({ log, wsConnected, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [log?.length]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-header">
        <span className="panel-title">System Events</span>
        <span style={{ fontSize: 11, color: wsConnected ? 'var(--status-online)' : 'var(--text-faint)' }}>
          {wsConnected ? 'Connected' : 'Offline'}
        </span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {loading ? (
          <div style={{ padding: 16, color: 'var(--text-faint)' }}>Loading events…</div>
        ) : !Array.isArray(log) || log.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-faint)' }}>
            No recent events
          </div>
        ) : (
          [...log].reverse().map((entry, i) => (
            <EventRow key={entry.id || i} entry={entry} />
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function EventRow({ entry }) {
  const sev = SEV[entry.severity] || SEV.INFO;
  const timeStr = entry.logged_at
    ? new Date(entry.logged_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className="fade-in" style={{
      padding: '12px 16px',
      borderBottom: 'var(--border-subtle)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: sev.color, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{sev.label}</span>
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{timeStr}</span>
        </div>
      </div>
      
      {entry.cell_name && (
        <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 4, letterSpacing: '-0.01em' }}>
          {entry.cell_name}
        </div>
      )}
      <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', lineHeight: 1.5 }}>
        {entry.message}
      </div>
    </div>
  );
}
