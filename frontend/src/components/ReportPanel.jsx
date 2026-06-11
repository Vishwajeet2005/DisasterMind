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
      <div className="glass-panel report-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', position: 'relative', overflow: 'hidden' }}>
        {/* Cinematic scanning laser effect */}
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, height: '2px',
          background: 'linear-gradient(90deg, transparent, var(--text-cyan), transparent)',
          boxShadow: '0 0 20px var(--text-cyan), 0 0 40px var(--text-cyan)',
          animation: 'scan-laser 2s ease-in-out infinite alternate',
          opacity: 0.6
        }}></div>
        
        <div style={{ position: 'relative', marginBottom: 32 }}>
          {/* Pulsing Core */}
          <div style={{ 
            width: 80, height: 80, 
            borderRadius: '50%', 
            border: '2px dashed rgba(0, 229, 255, 0.3)',
            borderTopColor: 'var(--text-cyan)',
            animation: 'spin 3s linear infinite',
            position: 'absolute',
            top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)'
          }}></div>
          <div style={{ 
            width: 60, height: 60, 
            borderRadius: '50%', 
            border: '2px solid rgba(0, 229, 255, 0.1)',
            borderBottomColor: 'var(--text-cyan)',
            animation: 'spin 1.5s linear infinite reverse',
            position: 'absolute',
            top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)'
          }}></div>
          <ShieldAlert size={32} color="var(--text-cyan)" style={{ position: 'relative', zIndex: 2 }} />
        </div>
        
        <div className="mono" style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-cyan)', letterSpacing: 4, marginBottom: 12, textShadow: '0 0 10px rgba(0, 229, 255, 0.5)' }}>
          EXECUTING NEURAL SCAN
        </div>
        
        <div className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)', letterSpacing: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
          <span>SYNTHESIZING SATELLITE TELEMETRY...</span>
          <span style={{ opacity: 0.6 }}>RUNNING XGBOOST ENSEMBLE</span>
        </div>
        <style>
          {`
            @keyframes scan-laser {
              0% { top: 0%; opacity: 0.2; }
              50% { opacity: 0.8; }
              100% { top: 100%; opacity: 0.2; }
            }
          `}
        </style>
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
    <div className="glass-panel report-panel" style={{ position: 'relative' }}>
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
        padding: '10px 16px', backgroundColor: 'rgba(0, 229, 255, 0.1)', border: '1px solid rgba(0, 229, 255, 0.3)',
        color: '#00E5FF', borderRadius: 'var(--radius-sm)', fontSize: 12, fontWeight: 700,
        marginBottom: 24, boxShadow: '0 0 10px rgba(0, 229, 255, 0.1)', textShadow: '0 0 5px rgba(0,229,255,0.5)'
      }}>
        {sr?.ml_validated ? <CheckCircle size={16} color="#00E5FF" /> : <AlertTriangle size={16} color="#FF6B00" />}
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
