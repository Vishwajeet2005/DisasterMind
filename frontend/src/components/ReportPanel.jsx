import React from 'react';
import { ShieldAlert, Download, FileText, AlertTriangle, CheckCircle } from 'lucide-react';
import API_CONFIG from '../api';

const ReportPanel = ({ report, loading, error }) => {
  const handleDownloadPDF = async () => {
    if (!report) return;
    try {
      const response = await fetch(`${API_CONFIG}/report/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis: report })
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
      <div className="glass-panel report-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <div style={{ position: 'relative', marginBottom: 24 }}>
          {/* Clean minimal spinner */}
          <div style={{ 
            width: 48, height: 48, 
            borderRadius: '50%', 
            border: '3px solid rgba(37, 99, 235, 0.1)',
            borderTopColor: 'var(--accent-primary)',
            animation: 'spin 1s ease-in-out infinite'
          }}></div>
        </div>
        
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
          Analyzing Telemetry
        </div>
        
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', textAlign: 'center' }}>
          Processing satellite and meteorological data...
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="glass-panel report-panel">
        <div className="empty-state">No active analysis generated.</div>
      </div>
    );
  }

  const sr = report.situation_report;
  const riskColorVar = `var(--color-${sr?.risk_level?.toLowerCase() || 'low'})`;
  const riskBgVar = `var(--bg-${sr?.risk_level?.toLowerCase() || 'low'})`;
  const riskBorderVar = `var(--border-${sr?.risk_level?.toLowerCase() || 'low'})`;

  return (
    <article className="glass-panel report-panel" aria-label="Tactical Intelligence Report" style={{ position: 'relative' }}>
      <div className="panel-header" style={{ justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldAlert size={16} /> Tactical Intelligence Report
        </div>
        <button 
          aria-label="Export Situation Report to PDF"
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
        padding: '10px 16px', backgroundColor: 'rgba(37, 99, 235, 0.05)', border: '1px solid rgba(37, 99, 235, 0.15)',
        color: 'var(--accent-primary)', borderRadius: 'var(--radius-sm)', fontSize: 12, fontWeight: 700,
        marginBottom: 24
      }}>
        {sr?.ml_validated ? <CheckCircle size={16} color="var(--accent-primary)" /> : <AlertTriangle size={16} color="var(--accent-warning)" />}
        <span>{sr?.ml_validated ? "VALIDATED" : "NOT VALIDATED"} BY XGBOOST & RANDOM FOREST ENSEMBLE</span>
      </div>

      {/* Summary */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Situation Summary</h2>
        <div style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text-primary)' }}>{sr?.situation_summary}</div>
      </div>
      
      {/* Priority Zones mapped to cards with specific urgency pill colors */}
      {sr?.priority_zones?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ margin: 0, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Priority Rescue Zones</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {sr.priority_zones.map((z, i) => (
              <div key={i} style={{ 
                padding: 12, border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg-primary)', display: 'flex', flexDirection: 'column', gap: 6
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>{z.name}</h3>
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

      {report?.satellite_thumbnail && (typeof report.satellite_thumbnail === 'string' || report.satellite_thumbnail.true_color) && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ margin: 0, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Satellite Intelligence (Earth Engine)</h2>
          <div style={{ 
            border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden',
            backgroundColor: 'var(--bg-primary)', padding: 4, display: 'flex', gap: 4
          }}>
            <img 
              src={typeof report.satellite_thumbnail === 'string' ? report.satellite_thumbnail : report.satellite_thumbnail.true_color} 
              alt="Google Earth Engine True Color" 
              style={{ width: typeof report.satellite_thumbnail === 'object' && report.satellite_thumbnail.false_color ? '50%' : '100%', height: 'auto', display: 'block', borderRadius: 'var(--radius-sm)' }}
            />
            {typeof report.satellite_thumbnail === 'object' && report.satellite_thumbnail.false_color && (
              <img 
                src={report.satellite_thumbnail.false_color} 
                alt="Google Earth Engine False Color (SAR/NIR)" 
                style={{ width: '50%', height: 'auto', display: 'block', borderRadius: 'var(--radius-sm)' }}
              />
            )}
          </div>
        </div>
      )}

      {/* Clean data tables for Resources and Timeline */}
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Action Timeline (24h)</h2>
        <div style={{ border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
          {sr?.action_timeline?.map((act, i) => (
            <div key={i} style={{ 
              display: 'flex', padding: '12px', backgroundColor: i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-primary)',
              borderBottom: i !== sr.action_timeline.length - 1 ? 'var(--border-subtle)' : 'none',
              alignItems: 'flex-start', gap: 16
            }}>
              <div className="mono" style={{ width: 70, fontSize: 12, fontWeight: 600, color: 'var(--color-high)' }}>{act.hour}</div>
              <div style={{ flex: 1, fontSize: 13, lineHeight: 1.5 }}>{act.action}</div>
            </div>
          ))}
        </div>
        </section>
      
      {sr?.resources_required && Object.keys(sr.resources_required).length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ margin: 0, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Required Resources</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(sr.resources_required).map(([res, count], i) => (
              <div key={i} style={{ 
                padding: '6px 12px', border: 'var(--border-subtle)', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-primary)', fontSize: 12, fontWeight: 500, color: 'var(--text-primary)',
                textTransform: 'capitalize'
              }}>
                {res.replace('_', ' ')}: {count}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-inverse-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
        <FileText size={12}/> Automatically generated by DisasterMind Autonomous Engine.
      </div>
    </article>
  );
};

export default ReportPanel;
