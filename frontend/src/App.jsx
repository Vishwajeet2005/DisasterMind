import React, { useState, useEffect } from 'react';
import IndiaMap from './components/IndiaMap';
import ThreatRoster from './components/ThreatRoster';
import AgentFeed from './components/AgentFeed';
import LiveReadings from './components/LiveReadings';
import CellDetailPanel from './components/CellDetailPanel';

import './styles/tokens.css';
import './App.css';

import API_CONFIG from './api';
const API_BASE = `${API_CONFIG}/api/monitor`;

export default function App() {
  const [gridCells, setGridCells] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);
  const [agentLog, setAgentLog] = useState([]);
  const [threats, setThreats] = useState([]);
  const [nationalTrend, setNationalTrend] = useState(null);
  const [lastRun, setLastRun] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);

  const [selectedCell, setSelectedCell] = useState(null);
  const [selectedRisk, setSelectedRisk] = useState(null);

  const [wsConnected, setWsConnected] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [isScanning, setIsScanning] = useState(false);

  // Fetch static grid once — with exponential retry so Render cold-start doesn't freeze the UI
  useEffect(() => {
    let retries = 0;
    const fetchGrid = () => {
      fetch(`${API_BASE}/grid?v=2.0`)
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(d => {
          setGridCells(Array.isArray(d) ? d : []);
          setLoadingInitial(false);
        })
        .catch(err => {
          console.error('[Grid] Fetch failed:', err);
          if (retries < 5) {
            retries++;
            setTimeout(fetchGrid, 3000 * retries); // 3s, 6s, 9s, 12s, 15s
          } else {
            setLoadingInitial(false); // Unblock UI after 5 failures — show map with no cells
          }
        });
    };
    fetchGrid();
  }, []);

  // Fast poll for heatmap, log, threats
  useEffect(() => {
    const fetchFast = () => {
      fetch(`${API_BASE}/heatmap`)
        .then(r => r.json())
        .then(d => setHeatmapData(Array.isArray(d) ? d : []))
        .catch(console.error);

      fetch(`${API_BASE}/feed`)
        .then(r => { setWsConnected(true); return r.json(); })
        .then(d => setAgentLog(Array.isArray(d) ? d : []))
        .catch(() => setWsConnected(false));

      fetch(`${API_BASE}/threats`)
        .then(r => r.json())
        .then(d => setThreats(Array.isArray(d) ? d : []))
        .catch(console.error);

      fetch(`${API_BASE}/status`)
        .then(r => r.json())
        .then(d => {
          setNationalTrend(d?.national_trend || null);
          setLastRun(d?.last_run || null);
          setSchedulerStatus(d?.scheduler || null);
          setIsScanning(d?.scheduler?.monitor_active || false);
        })
        .catch(console.error);
    };

    fetchFast();
    const id = setInterval(fetchFast, 5000);
    return () => clearInterval(id);
  }, []);

  // Handle cell click from map
  const handleCellSelect = (cell, risk) => {
    setSelectedCell(cell);
    setSelectedRisk(risk);
  };

  const handleThreatSelect = (threat) => {
    const cell = gridCells.find(c => c.cell_id === threat.cell_id) || threat;
    setSelectedCell(cell);
    setSelectedRisk(threat.risk_level);
  };

  const handleTriggerScan = async () => {
    if (isScanning) return;
    setIsScanning(true);
    try {
      await fetch(`${API_CONFIG}/api/monitor/scan`, { 
        method: 'POST',
        headers: { 'X-API-Key': import.meta.env.VITE_API_KEY || 'DISASTERMIND_SECRET_KEY_2026' }
      });
      // The scan takes about 60 seconds in the background. 
      // Reset the button so the user isn't permanently locked out.
      setTimeout(() => {
        setIsScanning(false);
      }, 3000);
    } catch (e) {
      console.error(e);
      setIsScanning(false);
    }
  };

  const handleDemoInject = async () => {
    try {
      await fetch(`${API_CONFIG}/api/demo/inject`);
      window.location.reload();
    } catch (e) {
      console.error(e);
    }
  };

  const statusColor = {
    SEVERE:   'var(--risk-critical-color)',
    ELEVATED: 'var(--risk-high-color)',
    WATCH:    'var(--risk-moderate-color)',
    NORMAL:   'var(--status-online)',
  }[nationalTrend?.status || 'NORMAL'] || 'var(--status-online)';

  return (
    <div className="app-shell">
      
      {/* ── Background Map ──────────────────────────────────── */}
      <div className="map-bg">
        <IndiaMap
          gridCells={gridCells}
          heatmapData={heatmapData}
          selectedCell={selectedCell}
          onCellClick={handleCellSelect}
        />
      </div>

      {/* ── Floating Topbar ─────────────────────────────────── */}
      <header className="topbar-float">
        <div className="brand-pill">
          <span className="brand-text">DisasterMind</span>
        </div>

        <div className="status-group">
          <div className="status-item">
            <div className="status-dot" style={{ background: statusColor }} />
            <span className="status-label">{nationalTrend?.status || 'Normal'} Status</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn-scan"
            style={{ 
              background: 'var(--risk-high-bg)', 
              color: 'var(--risk-high-color)', 
              borderColor: 'var(--risk-high-border)',
              marginRight: '8px'
            }}
            onClick={handleDemoInject}
          >
            Load Demo Data
          </button>
          <button
            className="btn-scan"
            onClick={handleTriggerScan}
            disabled={isScanning}
          >
            {isScanning ? (
              <>
                <span className="spin" style={{ display: 'inline-block', width: 12, height: 12, border: '2px solid rgba(0,0,0,0.2)', borderTopColor: '#000', borderRadius: '50%' }} />
                Scanning
              </>
            ) : (
              'Initiate Scan'
            )}
          </button>
        </div>
      </header>

      {/* ── Floating Side Panels ────────────────────────────── */}
      <div className="panel-float panel-left">
        <ThreatRoster
          threats={threats}
          selectedCell={selectedCell}
          onSelect={handleThreatSelect}
          loading={loadingInitial}
        />
      </div>

      <div className="panel-float panel-right" style={{
        width: selectedCell ? 480 : 320,
        transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>
        {selectedCell ? (
          <CellDetailPanel
            cell={selectedCell}
            riskLevel={selectedRisk}
            onClose={() => setSelectedCell(null)}
          />
        ) : (
          <AgentFeed
            log={agentLog}
            wsConnected={wsConnected}
            loading={loadingInitial}
          />
        )}
      </div>

      {/* ── Floating Bottom Pill ────────────────────────────── */}
      <LiveReadings
        nationalTrend={nationalTrend}
        lastRun={lastRun}
        schedulerStatus={schedulerStatus}
      />
    </div>
  );
}
