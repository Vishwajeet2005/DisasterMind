import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu, AlertTriangle, ThermometerSun, CloudRain, Truck, Crosshair } from 'lucide-react';
import MapView from './components/MapView';
import SearchBar from './components/SearchBar';
import ReportPanel from './components/ReportPanel';

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

  const handleRunAnalysis = async (region) => {
    if (!region) return;
    
    setLoading(true);
    setError(null);
    setReport(null);
    
    try {
      const payload = {
        region_name: region.name,
        lat: region.lat,
        lon: region.lon,
        bbox: {
          lat_min: region.bbox[0],
          lon_min: region.bbox[1],
          lat_max: region.bbox[2],
          lon_max: region.bbox[3]
        }
      };

      const response = await fetch(`http://localhost:8000/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      
      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRegion = (region) => {
    setSelectedRegion(region);
    handleRunAnalysis(region);
  };

  const renderDashboardPanel = () => {
    if (loading) return null;
    
    if (error) {
      return (
        <div className="glass-panel dashboard-panel">
          <div className="error-state">
            <AlertTriangle size={32} style={{ marginBottom: 16 }} />
            <div>System Error: {error}</div>
          </div>
        </div>
      );
    }

    if (!report) {
      return (
        <div className="glass-panel dashboard-panel">
          <div className="empty-state">Awaiting region target and analysis execution</div>
        </div>
      );
    }

    const { raw_data, ml_prediction } = report;
    const precip = raw_data?.weather?.daily?.precipitation_sum?.[0] || 0;
    const roadCount = raw_data?.roads?.total_count || 0;
    const floodProb = (ml_prediction?.flood_probability * 100).toFixed(1) || 0;
    const severity = (ml_prediction?.severity_score * 10).toFixed(1) || 0;

    return (
      <div className="glass-panel dashboard-panel">
        <div className="panel-header"><Activity size={16} /> Live Telemetry: {selectedRegion?.name}</div>
        <div className="metric-grid">
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><CloudRain size={12}/> Precipitation</div>
            <div className="metric-value">{precip} <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>mm/day</span></div>
            <div style={{ height: 4, width: '100%', backgroundColor: '#E2E8F0', marginTop: 8, borderRadius: 2 }}>
              <div style={{ height: '100%', width: `${Math.min(precip, 100)}%`, backgroundColor: precip > 50 ? 'var(--color-critical)' : '#3B82F6', borderRadius: 2 }}></div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Cpu size={12}/> ML Flood Risk</div>
            <div className="metric-value" style={{ color: floodProb > 50 ? 'var(--color-critical)' : 'var(--color-low)'}}>{floodProb}%</div>
            <div style={{ height: 4, width: '100%', backgroundColor: '#E2E8F0', marginTop: 8, borderRadius: 2 }}>
              <div style={{ height: '100%', width: `${floodProb}%`, backgroundColor: floodProb > 50 ? 'var(--color-critical)' : 'var(--color-low)', borderRadius: 2 }}></div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><AlertTriangle size={12}/> Threat Severity</div>
            <div className="metric-value">{severity} <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>/ 10</span></div>
            <div style={{ height: 4, width: '100%', backgroundColor: '#E2E8F0', marginTop: 8, borderRadius: 2 }}>
              <div style={{ height: '100%', width: `${severity * 10}%`, backgroundColor: severity > 7 ? 'var(--color-critical)' : 'var(--color-moderate)', borderRadius: 2 }}></div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Truck size={12}/> Usable Roads</div>
            <div className="metric-value">{roadCount}</div>
            <div style={{ fontSize: 10, marginTop: 4, color: 'var(--text-secondary)' }}>{raw_data?.roads?.accessibility || 'UNKNOWN'} ACCESSIBILITY</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Immersive Map Background Layer */}
      <div className="map-background">
        <MapView 
          selectedRegion={selectedRegion} 
          onSelectRegion={handleSelectRegion} 
          riskLevel={report?.situation_report?.risk_level} 
        />
      </div>

      {/* Floating HUD Layer */}
      <div className="hud-layer">
        
        {/* Topbar Command Strip */}
        <div className="floating-topbar hud-interactive">
          <div className="topbar-brand">
            <Activity className="brand-icon" size={18} />
            <span>DISASTERMIND</span>
          </div>
          <div className="topbar-status">
            <span>{currentTime}</span>
            <div className="status-indicator">
              <div className="dot" style={{ backgroundColor: loading ? 'var(--accent-warning)' : 'var(--accent-safe)', boxShadow: `0 0 8px ${loading ? 'var(--accent-warning)' : 'var(--accent-safe)'}`}}></div>
              <span>{loading ? 'ANALYSIS_ACTIVE' : 'SYSTEM_NOMINAL'}</span>
            </div>
          </div>
        </div>

        {/* Floating Search Pill */}
        <div className="hud-interactive" style={{ position: 'absolute', top: 24, left: 24, width: 360 }}>
          <SearchBar onSearch={handleSelectRegion} />
        </div>

        {/* Floating Right Sidebar */}
        <div className="floating-sidebar hud-interactive">
          {renderDashboardPanel()}
          <ReportPanel report={report} loading={loading} error={error} />
        </div>
      </div>
    </div>
  );
};

export default App;
