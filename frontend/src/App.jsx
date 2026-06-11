import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu, AlertTriangle, ThermometerSun, CloudRain, Users, Truck } from 'lucide-react';
import MapView from './components/MapView';
import './styles/tokens.css';
import './App.css';

import ReportPanel from './components/ReportPanel';

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
      const response = await fetch(`http://localhost:8000/demo/${region.id}`);
      if (!response.ok) {
        throw new Error("Demo cache not found or API unavailable");
      }
      const data = await response.json();
      
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

  return (
    <div className="app-container">
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

      <div className="main-content">
        <div className="panel-left surface-panel" style={{ padding: 0 }}>
          <MapView 
            selectedRegion={selectedRegion} 
            onSelectRegion={handleSelectRegion} 
            riskLevel={report?.situation_report?.risk_level} 
          />
        </div>
        
        <div className="panel-right">
          {renderDashboardPanel()}
          <ReportPanel report={report} loading={loading} error={error} />
        </div>
      </div>
    </div>
  );
};

export default App;
