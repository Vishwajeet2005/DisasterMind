import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu, AlertTriangle, ThermometerSun, CloudRain, Users, Truck } from 'lucide-react';
import MapView from './components/MapView';
import './styles/tokens.css';
import './App.css';

const App = () => {
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false, timeZone: 'UTC' }) + ' UTC');

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString('en-US', { hour12: false, timeZone: 'UTC' }) + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSelectRegion = async (region) => {
    setSelectedRegion(region);
    setLoading(true);
    setError(null);
    setReport(null);
    
    try {
      // Trying to fetch the pre-cached demo data from our backend
      const response = await fetch(`http://localhost:8000/demo/${region.id}`);
      if (!response.ok) {
        throw new Error("Demo cache not found or API unavailable");
      }
      const data = await response.json();
      
      // Simulate slight delay to show off skeletons
      setTimeout(() => {
        setReport(data);
        setLoading(false);
      }, 1000);
      
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const renderDashboardPanel = () => {
    if (loading) {
      return (
        <div className="surface-panel dashboard-panel">
          <div className="panel-header"><Activity size={16} /> Live Telemetry</div>
          <div className="metric-grid">
            <div className="skeleton skeleton-box"></div>
            <div className="skeleton skeleton-box"></div>
            <div className="skeleton skeleton-box"></div>
            <div className="skeleton skeleton-box"></div>
          </div>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="surface-panel dashboard-panel">
          <div className="error-state">
            <AlertTriangle size={32} style={{ marginBottom: 16 }} />
            <div>System Error: {error}</div>
          </div>
        </div>
      );
    }

    if (!report) {
      return (
        <div className="surface-panel dashboard-panel">
          <div className="empty-state">Awaiting regional selection</div>
        </div>
      );
    }

    const { raw_data, ml_prediction } = report;
    const precip = raw_data?.weather?.daily?.precipitation_sum?.[0] || 0;
    const roadCount = raw_data?.roads?.total_count || 0;
    const floodProb = (ml_prediction?.flood_probability * 100).toFixed(1) || 0;

    return (
      <div className="surface-panel dashboard-panel">
        <div className="panel-header"><Activity size={16} /> Live Telemetry: {selectedRegion?.name}</div>
        <div className="metric-grid">
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><CloudRain size={12}/> Precipitation</div>
            <div className="metric-value">{precip} mm</div>
          </div>
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Cpu size={12}/> ML Flood Prob</div>
            <div className="metric-value" style={{ color: floodProb > 50 ? 'var(--color-critical)' : 'var(--color-low)'}}>{floodProb}%</div>
          </div>
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><ThermometerSun size={12}/> Avg Elevation</div>
            <div className="metric-value">{raw_data?.elevation?.avg?.toFixed(0) || '--'} m</div>
          </div>
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Truck size={12}/> Major Roads</div>
            <div className="metric-value">{roadCount}</div>
          </div>
        </div>
      </div>
    );
  };

  const renderReportPanel = () => {
    if (loading) {
      return (
        <div className="surface-panel report-panel">
          <div className="panel-header"><ShieldAlert size={16} /> Tactical Intelligence Report</div>
          <div className="skeleton skeleton-text" style={{ height: 24, width: '40%' }}></div>
          <div className="skeleton skeleton-text" style={{ height: 60, marginTop: 16 }}></div>
          <div className="skeleton skeleton-text" style={{ height: 100, marginTop: 16 }}></div>
          <div className="skeleton skeleton-text" style={{ height: 40, marginTop: 16 }}></div>
        </div>
      );
    }

    if (!report) {
      return (
        <div className="surface-panel report-panel">
          <div className="empty-state">No active analysis</div>
        </div>
      );
    }

    const sr = report.situation_report;
    const riskColorVar = `var(--color-${sr?.risk_level?.toLowerCase() || 'low'})`;
    const riskBgVar = `var(--bg-${sr?.risk_level?.toLowerCase() || 'low'})`;
    const riskBorderVar = `var(--border-${sr?.risk_level?.toLowerCase() || 'low'})`;

    return (
      <div className="surface-panel report-panel">
        <div className="panel-header"><ShieldAlert size={16} /> Tactical Intelligence Report</div>
        
        {/* Risk Banner */}
        <div style={{ 
          padding: 16, 
          backgroundColor: riskBgVar, 
          border: riskBorderVar, 
          borderRadius: 'var(--radius-md)',
          color: riskColorVar,
          fontWeight: 700,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16
        }}>
          <span>RISK: {sr?.risk_level}</span>
          <span className="mono">SCORE: {sr?.risk_score}</span>
        </div>

        {/* Summary */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Situation Summary</div>
          <div style={{ fontSize: 14, lineHeight: 1.5 }}>{sr?.situation_summary}</div>
        </div>

        {/* Actions Timeline */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Action Timeline</div>
          <div style={{ border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
            {sr?.action_timeline?.map((act, i) => (
              <div key={i} style={{ 
                display: 'flex', 
                padding: '10px 12px', 
                borderBottom: i !== sr.action_timeline.length - 1 ? 'var(--border-subtle)' : 'none',
                fontSize: 13
              }}>
                <div className="mono" style={{ width: '80px', fontWeight: 600, color: 'var(--text-secondary)' }}>{act.timeframe}</div>
                <div style={{ flex: 1 }}>{act.action}</div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Priority Zones */}
        {sr?.priority_zones?.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>Priority Zones</div>
            <ul style={{ paddingLeft: 20, fontSize: 13, lineHeight: 1.6 }}>
              {sr.priority_zones.map((z, i) => (
                <li key={i}><strong>{z.zone_name}</strong>: {z.reason}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Topbar */}
      <div className="topbar">
        <div className="topbar-brand">
          <Activity className="brand-icon" size={20} />
          <span>DISASTERMIND</span>
        </div>
        <div className="topbar-status">
          <span>{currentTime}</span>
          <div className="status-indicator">
            <div className="dot"></div>
            <span>SYSTEM_NOMINAL</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="panel-left surface-panel" style={{ padding: 0 }}>
          <MapView selectedRegion={selectedRegion} onSelectRegion={handleSelectRegion} />
        </div>
        
        <div className="panel-right">
          {renderDashboardPanel()}
          {renderReportPanel()}
        </div>
      </div>
    </div>
  );
};

export default App;
