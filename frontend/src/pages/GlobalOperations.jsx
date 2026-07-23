import React, { useState, useEffect } from 'react';
import { Search, Filter, MoreHorizontal, Settings, ListPlus } from 'lucide-react';
import IndiaMap from '../components/IndiaMap';
import API_CONFIG from '../api';

const API_BASE = `${API_CONFIG}/api/monitor`;

export default function GlobalOperations() {
  const [gridCells, setGridCells] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);
  const [agentLog, setAgentLog] = useState([]);
  
  const [selectedCell, setSelectedCell] = useState(null);
  const [selectedRisk, setSelectedRisk] = useState(null);

  // Fetch static grid once
  useEffect(() => {
    let retries = 0;
    const fetchGrid = () => {
      fetch(`${API_BASE}/grid?v=2.0`)
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(d => {
          setGridCells(Array.isArray(d) ? d : []);
        })
        .catch(err => {
          console.error('[Grid] Fetch failed:', err);
          if (retries < 5) {
            retries++;
            setTimeout(fetchGrid, 3000 * retries);
          }
        });
    };
    fetchGrid();
  }, []);

  // Fast poll for heatmap and logs
  useEffect(() => {
    const fetchFast = () => {
      fetch(`${API_BASE}/heatmap`)
        .then(r => r.json())
        .then(d => setHeatmapData(Array.isArray(d) ? d : []))
        .catch(console.error);

      fetch(`${API_BASE}/feed`)
        .then(r => r.json())
        .then(d => setAgentLog(Array.isArray(d) ? d : []))
        .catch(console.error);
    };

    fetchFast();
    const id = setInterval(fetchFast, 5000);
    return () => clearInterval(id);
  }, []);

  const handleCellSelect = (cell, risk) => {
    setSelectedCell(cell);
    setSelectedRisk(risk);
  };

  return (
    <>
      {/* Left: Interactive Map Canvas */}
      <section className="flex-[7] relative bg-surface-container-lowest overflow-hidden">
        {/* Tactical Grid Overlay */}
        <div className="absolute inset-0 tactical-grid pointer-events-none z-0"></div>
        
        {/* The actual Leaflet Map */}
        <div className="absolute inset-0 z-0">
          <IndiaMap 
            gridCells={gridCells}
            heatmapData={heatmapData}
            onCellSelect={handleCellSelect}
          />
        </div>

        {/* Floating Command Palette */}
        <div className="absolute top-container-margin left-container-margin w-[480px] bg-surface-container-low border border-outline-variant z-10 flex flex-col backdrop-blur-sm shadow-none">
          <div className="flex items-center border-b border-outline-variant px-4 h-12 bg-surface">
            <Search className="text-on-surface-variant mr-3" size={18} />
            <input 
              autoFocus 
              className="bg-transparent border-none w-full text-primary font-data-tabular text-[13px] focus:ring-0 placeholder:text-on-surface-variant outline-none" 
              placeholder="ENTER COORDINATES OR ENTITY ID..." 
              type="text"
            />
            <div className="flex items-center gap-2 font-label-caps text-[9px] text-on-surface-variant ml-2 border border-outline-variant px-1.5 py-0.5">
              <span>CTRL</span><span>K</span>
            </div>
          </div>
          
          <div className="p-3 bg-surface-container-low flex flex-wrap gap-2">
            <button className="border border-outline-variant px-3 py-1 font-label-caps text-[11px] text-on-surface hover:bg-surface hover:text-primary flex items-center gap-1 bg-surface-container transition-none">
              <Filter size={14} />
              SECTOR: ALL
            </button>
            <button className="border border-primary px-3 py-1 font-label-caps text-[11px] bg-primary text-on-primary hover:bg-surface-bright transition-none">
              STATUS: CRITICAL
            </button>
            <button className="border border-outline-variant px-3 py-1 font-label-caps text-[11px] text-on-surface hover:bg-surface hover:text-primary transition-none">
              ASSETS: DEPLOYED
            </button>
          </div>
        </div>

        {/* Bottom Left Telemetry Overlay */}
        <div className="absolute bottom-container-margin left-container-margin flex flex-col gap-1 z-10 pointer-events-none">
          <div className="font-data-tabular text-[11px] text-on-surface-variant tracking-widest uppercase">Global Coordinates</div>
          <div className="font-data-tabular text-[14px] text-primary">
            {selectedCell 
              ? `LAT: ${selectedCell.lat.toFixed(4)}° / LNG: ${selectedCell.lon.toFixed(4)}°` 
              : "LAT: 45.9281° / LNG: -12.3940°"}
          </div>
          <div className="font-data-tabular text-[11px] text-on-surface-variant mt-2 flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></div>
            LINK SECURE
          </div>
        </div>
      </section>

      {/* Right: Slim Drawer (Event Feed) */}
      <aside className="flex-[3] min-w-[320px] max-w-[480px] bg-surface-container border-l border-outline-variant flex flex-col h-full z-20">
        <header className="h-12 border-b border-outline-variant flex items-center justify-between px-4 bg-surface-container-lowest flex-shrink-0">
          <div className="flex items-center gap-2">
            <ListPlus className="text-primary" size={18} />
            <h2 className="font-label-caps text-[11px] text-primary tracking-widest">AUTONOMOUS EVENT FEED</h2>
          </div>
          <div className="flex items-center gap-1 font-data-tabular text-[10px] text-on-surface-variant border border-outline-variant px-1 bg-surface-container">
            <span className="w-1.5 h-1.5 bg-secondary-container rounded-none block"></span>
            LIVE
          </div>
        </header>

        <div className="h-8 border-b border-outline-variant flex bg-surface flex-shrink-0">
          <button className="flex-1 font-label-caps text-[10px] text-on-surface border-r border-outline-variant hover:bg-surface-container-highest transition-none">ALL LOGS</button>
          <button className="flex-1 font-label-caps text-[10px] text-on-surface-variant border-r border-outline-variant hover:bg-surface-container-highest transition-none">ALERTS ONLY</button>
          <button className="w-10 flex items-center justify-center hover:bg-surface-container-highest transition-none text-on-surface-variant">
            <MoreHorizontal size={14} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {agentLog.length === 0 ? (
            <div className="text-center font-data-tabular text-[12px] text-on-surface-variant mt-10">No logs available</div>
          ) : (
            agentLog.map((log) => {
              const time = new Date(log.logged_at).toLocaleTimeString('en-US', { hour12: false, timeZone: 'UTC' }) + ' UTC';
              const isError = log.severity === 'ERROR' || log.severity === 'CRITICAL';
              const isWarning = log.severity === 'WARNING';
              
              let containerClass = "border bg-surface flex flex-col p-3 hover:bg-surface-container-highest cursor-pointer group ";
              let timeClass = "font-data-tabular text-[11px] font-bold ";
              
              if (isError) {
                containerClass += "border-error-container";
                timeClass += "text-error";
              } else if (isWarning) {
                containerClass += "border-outline-variant";
                timeClass += "text-on-surface";
              } else {
                containerClass += "border-outline-variant";
                timeClass += "text-on-surface-variant";
              }

              return (
                <div key={log.id} className={containerClass}>
                  <div className="flex justify-between items-start mb-2">
                    <span className={timeClass}>{time}</span>
                    {log.cell_id && (
                      <span className={`border px-1 text-[9px] font-label-caps ${isError ? 'border-error text-error bg-error-container' : 'border-outline-variant text-on-surface-variant bg-surface'}`}>
                        {log.cell_id}
                      </span>
                    )}
                  </div>
                  <div className={`font-body-md text-[13px] ${isError ? 'text-on-background' : 'text-on-surface'} leading-tight`}>
                    {log.message}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
}
