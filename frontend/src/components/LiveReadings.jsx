import React, { useState, useEffect } from 'react';

export default function LiveReadings({ nationalTrend, lastRun, schedulerStatus }) {
  const [now, setNow] = useState(new Date());
  const [countdown, setCountdown] = useState('');

  // Live clock
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  // Countdown to next scan
  useEffect(() => {
    if (!schedulerStatus?.next_scan) return;
    const update = () => {
      const diff = new Date(schedulerStatus.next_scan) - new Date();
      if (diff <= 0) { setCountdown('Scanning'); return; }
      const m = Math.floor(diff / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setCountdown(`Next scan in ${m}m ${String(s).padStart(2, '0')}s`);
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [schedulerStatus?.next_scan]);

  const activeCount   = nationalTrend?.active_threats || 0;
  const criticalCount = nationalTrend?.critical_count || 0;
  
  const lastScanStr = lastRun?.completed_at
    ? new Date(lastRun.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : 'Pending';

  return (
    <div className="bottom-pill fade-in">
      
      {/* Metric: Current Time */}
      <div className="bottom-metric">
        <span className="bottom-label">Time</span>
        <span className="bottom-value text-muted" style={{ fontVariantNumeric: 'tabular-nums' }}>
          {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>
      </div>

      {/* Metric 1 */}
      <div className="bottom-metric">
        <span className="bottom-label">Threats</span>
        <span className="bottom-value" style={{ color: activeCount > 0 ? 'var(--risk-high-color)' : 'var(--text-primary)' }}>
          {activeCount}
        </span>
      </div>

      {/* Metric 2 */}
      <div className="bottom-metric">
        <span className="bottom-label">Critical</span>
        <span className="bottom-value" style={{ color: criticalCount > 0 ? 'var(--risk-critical-color)' : 'var(--text-primary)' }}>
          {criticalCount}
        </span>
      </div>

      {/* Metric 3 */}
      <div className="bottom-metric">
        <span className="bottom-label">Last updated</span>
        <span className="bottom-value text-muted">{lastScanStr}</span>
      </div>

      {/* Metric 4 */}
      <div className="bottom-metric">
        <span className="bottom-label" style={{ color: 'var(--accent)' }}>{countdown || 'Idle'}</span>
      </div>

    </div>
  );
}
