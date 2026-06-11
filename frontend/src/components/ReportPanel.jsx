import React from 'react';
import { ShieldAlert, Download, FileText, AlertTriangle, CheckCircle } from 'lucide-react';

const ReportPanel = ({ report, loading, error }) => {
  const handleDownloadPDF = async () => {
    if (!report) return;
    try {
      const response = await fetch('http://localhost:8000/report/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report)
      });
      if (!response.ok) throw new Error("Failed to generate PDF");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `DisasterMind_Report_${report.region_name || 'Analysis'}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(err);
      alert("Could not download PDF. Backend might be unavailable.");
    }
  };

  if (loading) {
    return (
      <div className="surface-panel report-panel">
        <div className="panel-header"><ShieldAlert size={16} /> Tactical Intelligence Report</div>
        {/* Risk Badge Skeleton */}
        <div className="skeleton" style={{ height: 72, width: '100%', borderRadius: 'var(--radius-md)', marginBottom: 16 }}></div>
        {/* ML Validation Strip Skeleton */}
        <div className="skeleton" style={{ height: 32, width: '100%', borderRadius: 'var(--radius-sm)', marginBottom: 20 }}></div>
        {/* Summary Skeleton */}
        <div className="skeleton skeleton-text"></div>
        <div className="skeleton skeleton-text"></div>
        <div className="skeleton skeleton-text short" style={{ marginBottom: 24 }}></div>
        {/* Zones Skeleton */}
        <div className="skeleton skeleton-box" style={{ height: 80 }}></div>
        <div className="skeleton skeleton-box" style={{ height: 120 }}></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="surface-panel report-panel">
        <div className="empty-state">No active analysis generated.</div>
      </div>
    );
  }

  const sr = report.situation_report;
  const riskColorVar = `var(--color-${sr?.risk_level?.toLowerCase() || 'low'})`;
  const riskBgVar = `var(--bg-${sr?.risk_level?.toLowerCase() || 'low'})`;
  const riskBorderVar = `var(--border-${sr?.risk_level?.toLowerCase() || 'low'})`;

  return (
    <div className="surface-panel report-panel" style={{ position: 'relative' }}>
      <div className="panel-header" style={{ justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldAlert size={16} /> Tactical Intelligence Report
        </div>
        <button 
          onClick={handleDownloadPDF}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '6px 12px', backgroundColor: 'var(--bg-sidebar)',
            color: 'var(--text-inverse)', border: 'none', borderRadius: 'var(--radius-md)',
            cursor: 'pointer', fontSize: 12, fontWeight: 500
          }}
        >
          <Download size={14} /> EXPORT PDF
        </button>
      </div>
      
      {/* Risk Level Badge (72px height, colored border, JetBrains Mono for score) */}
      <div style={{ 
        height: 72,
        padding: '0 20px', 
        backgroundColor: riskBgVar, 
        border: riskBorderVar, 
        borderRadius: 'var(--radius-md)',
        color: riskColorVar,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16
      }}>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: 11, fontWeight: 600, opacity: 0.8, textTransform: 'uppercase' }}>Overall Risk Level</span>
          <span style={{ fontSize: 24, fontWeight: 700 }}>{sr?.risk_level}</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <span style={{ fontSize: 11, fontWeight: 600, opacity: 0.8, textTransform: 'uppercase' }}>Threat Score</span>
          <span className="mono" style={{ fontSize: 24, fontWeight: 700 }}>{sr?.risk_score}/100</span>
        </div>
      </div>

      {/* ML Validation Strip */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 12px', backgroundColor: '#EFF6FF', border: '1px solid #BFDBFE',
        color: '#1E3A8A', borderRadius: 'var(--radius-sm)', fontSize: 12, fontWeight: 500,
        marginBottom: 20
      }}>
        {sr?.ml_validated ? <CheckCircle size={14} color="#2563EB" /> : <AlertTriangle size={14} color="#B45309" />}
        <span>{sr?.ml_validated ? "VALIDATED" : "NOT VALIDATED"} BY XGBOOST & RANDOM FOREST ENSEMBLE</span>
      </div>

      {/* Summary */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Situation Summary</div>
        <div style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text-primary)' }}>{sr?.situation_summary}</div>
      </div>
      
      {/* Priority Zones mapped to cards with specific urgency pill colors */}
      {sr?.priority_zones?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Priority Rescue Zones</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {sr.priority_zones.map((z, i) => (
              <div key={i} style={{ 
                padding: 12, border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg-primary)', display: 'flex', flexDirection: 'column', gap: 6
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{z.zone_name}</span>
                  <span style={{ 
                    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 12,
                    backgroundColor: 'var(--bg-critical)', color: 'var(--color-critical)'
                  }}>URGENT</span>
                </div>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{z.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {report?.satellite_thumbnail && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Satellite Intelligence (Earth Engine)</div>
          <div style={{ 
            border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden',
            backgroundColor: 'var(--bg-primary)', padding: 4
          }}>
            <img 
              src={report.satellite_thumbnail} 
              alt="Google Earth Engine Thumbnail" 
              style={{ width: '100%', height: 'auto', display: 'block', borderRadius: 'var(--radius-sm)' }}
            />
          </div>
        </div>
      )}

      {/* Clean data tables for Resources and Timeline */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Action Timeline (48HRS)</div>
        <div style={{ border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
          {sr?.action_timeline?.map((act, i) => (
            <div key={i} style={{ 
              display: 'flex', padding: '12px', backgroundColor: i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-primary)',
              borderBottom: i !== sr.action_timeline.length - 1 ? 'var(--border-subtle)' : 'none',
              alignItems: 'flex-start', gap: 16
            }}>
              <div className="mono" style={{ width: 70, fontSize: 12, fontWeight: 600, color: 'var(--color-high)' }}>{act.timeframe}</div>
              <div style={{ flex: 1, fontSize: 13, lineHeight: 1.5 }}>{act.action}</div>
            </div>
          ))}
        </div>
      </div>
      
      {sr?.resources_required?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Required Resources</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {sr.resources_required.map((res, i) => (
              <div key={i} style={{ 
                padding: '6px 12px', border: 'var(--border-subtle)', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-primary)', fontSize: 12, fontWeight: 500, color: 'var(--text-primary)'
              }}>
                {res}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-inverse-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
        <FileText size={12}/> Automatically generated by DisasterMind Autonomous Engine.
      </div>
    </div>
  );
};

export default ReportPanel;
