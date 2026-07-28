import React, { useState, useEffect } from 'react';
import { Search, Filter, MoreHorizontal, ListPlus, Activity } from 'lucide-react';
import IndiaMap from '../components/IndiaMap';
import CellDetailPanel from '../components/CellDetailPanel';
import API_CONFIG from '../api';

const API_BASE = `${API_CONFIG}/api/monitor`;

export default function GlobalOperations() {
  const [gridCells, setGridCells] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);
  const [agentLog, setAgentLog] = useState([]);
  const [feedFilter, setFeedFilter] = useState('ALL');
  const [showFeedMenu, setShowFeedMenu] = useState(false);
  
  const [selectedCell, setSelectedCell] = useState(null);
  const [selectedRisk, setSelectedRisk] = useState(null);

  // Command Palette State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('CRITICAL');
  const [sectorFilter, setSectorFilter] = useState('ALL');
  const [assetsFilter, setAssetsFilter] = useState('DEPLOYED');
  const [searchError, setSearchError] = useState(false);
  
  const searchInputRef = React.useRef(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearch = (e) => {
    if (e.key === 'Enter' && searchQuery.trim() !== '') {
      const q = searchQuery.trim().toLowerCase();
      const found = gridCells.find(c => 
        c.cell_id.toLowerCase() === q || 
        c.name.toLowerCase().includes(q) || 
        c.state.toLowerCase().includes(q)
      );

      if (found) {
        const threat = heatmapData.find(t => t.cell_id === found.cell_id);
        handleCellSelect(found, threat ? threat.risk_level : 'NONE');
        setSearchQuery('');
        setSearchError(false);
        searchInputRef.current?.blur();
      } else {
        setSearchError(true);
        setTimeout(() => setSearchError(false), 3000);
      }
    }
  };

  const cycleStatus = () => {
    const cycle = { 'CRITICAL': 'HIGH', 'HIGH': 'ALL', 'ALL': 'CRITICAL' };
    setStatusFilter(cycle[statusFilter] || 'ALL');
  };

  const cycleSector = () => {
    const cycle = { 'ALL': 'NORTH', 'NORTH': 'SOUTH', 'SOUTH': 'ALL' };
    setSectorFilter(cycle[sectorFilter] || 'ALL');
  };

  const cycleAssets = () => {
    const cycle = { 'DEPLOYED': 'STANDBY', 'STANDBY': 'OFFLINE', 'OFFLINE': 'DEPLOYED' };
    setAssetsFilter(cycle[assetsFilter] || 'DEPLOYED');
  };

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
            selectedCell={selectedCell}
            onCellClick={handleCellSelect}
          />
        </div>

        {/* Floating Command Palette */}
        <div className="absolute top-container-margin left-[80px] w-[480px] bg-surface-container-low border border-outline-variant z-10 flex flex-col backdrop-blur-sm shadow-none">
          <div className="flex items-center border-b border-outline-variant px-4 h-12 bg-surface">
            <Search className="text-on-surface-variant mr-3" size={18} />
            <input 
              ref={searchInputRef}
              autoFocus 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearch}
              className={`bg-transparent border-none w-full font-body-md text-[14px] focus:ring-0 outline-none ${searchError ? 'text-error placeholder:text-error/70' : 'text-primary placeholder:text-on-surface-variant'}`} 
              placeholder={searchError ? "No matching entities found in the active sector." : "Search by geographic coordinates or entity designation..."} 
              type="text"
            />
            <div className="flex items-center gap-2 font-label-caps text-[9px] text-on-surface-variant ml-2 border border-outline-variant px-1.5 py-0.5">
              <span>CTRL</span><span>K</span>
            </div>
          </div>
          
          <div className="p-3 bg-surface-container-low flex flex-wrap gap-2">
            <button 
              onClick={cycleSector}
              className={`border px-3 py-1 font-label-caps text-[11px] flex items-center gap-1 transition-opacity ${sectorFilter === 'ALL' ? 'border-outline-variant text-on-surface hover:bg-surface' : 'border-primary bg-primary text-on-primary hover:opacity-90'}`}
            >
              <Filter size={14} />
              SECTOR: {sectorFilter}
            </button>
            <button 
              onClick={cycleStatus}
              className={`border px-3 py-1 font-label-caps text-[11px] transition-opacity ${statusFilter === 'ALL' ? 'border-outline-variant text-on-surface hover:bg-surface' : 'border-primary bg-primary text-on-primary hover:opacity-90'}`}
            >
              STATUS: {statusFilter}
            </button>
            <button 
              onClick={cycleAssets}
              className={`border px-3 py-1 font-label-caps text-[11px] transition-opacity ${assetsFilter === 'ALL' ? 'border-outline-variant text-on-surface hover:bg-surface' : 'border-primary bg-primary text-on-primary hover:opacity-90'}`}
            >
              ASSETS: {assetsFilter}
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

      {/* Right: Slim Drawer (Event Feed or Detail Panel) */}
      {selectedCell ? (
        <CellDetailPanel 
          cell={selectedCell} 
          riskLevel={selectedRisk} 
          onClose={() => setSelectedCell(null)} 
        />
      ) : (
        <aside className="flex-[3] min-w-[320px] max-w-[480px] bg-surface-container/80 backdrop-blur-xl border-l border-outline-variant flex flex-col h-full z-20 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
          <header className="h-12 border-b border-outline-variant flex items-center justify-between px-4 bg-surface/50 backdrop-blur-md flex-shrink-0">
          <div className="flex items-center gap-2">
            <ListPlus className="text-primary" size={18} />
            <h2 className="font-label-caps text-[11px] text-primary tracking-widest">AUTONOMOUS EVENT FEED</h2>
          </div>
          <div className="flex items-center gap-1 font-data-tabular text-[10px] text-on-surface-variant border border-outline-variant px-1 bg-surface-container">
            <span className="w-1.5 h-1.5 bg-secondary-container rounded-none block"></span>
            LIVE
          </div>
        </header>

        <div className="h-8 border-b border-outline-variant flex bg-surface/50 backdrop-blur-md flex-shrink-0 relative">
          <button 
            onClick={() => setFeedFilter('ALL')}
            className={`flex-1 font-label-caps text-[10px] border-r border-outline-variant hover:bg-surface-container-highest transition-none ${feedFilter === 'ALL' ? 'text-on-surface bg-surface-container-highest' : 'text-on-surface-variant'}`}
          >
            ALL LOGS
          </button>
          <button 
            onClick={() => setFeedFilter('ALERTS')}
            className={`flex-1 font-label-caps text-[10px] border-r border-outline-variant hover:bg-surface-container-highest transition-none ${feedFilter === 'ALERTS' ? 'text-on-surface bg-surface-container-highest' : 'text-on-surface-variant'}`}
          >
            ALERTS ONLY
          </button>
          <button 
            onClick={() => setShowFeedMenu(!showFeedMenu)}
            className={`w-10 flex items-center justify-center transition-none ${showFeedMenu ? 'bg-surface-container-highest text-on-surface' : 'text-on-surface-variant hover:bg-surface-container-highest'}`}
          >
            <MoreHorizontal size={14} />
          </button>

          {showFeedMenu && (
            <div className="absolute top-8 right-0 w-48 bg-surface-container border border-outline-variant border-t-0 flex flex-col z-50 shadow-none">
              <button 
                onClick={() => { setAgentLog([]); setShowFeedMenu(false); }} 
                className="px-4 py-3 text-left font-label-caps text-[10px] text-on-surface hover:bg-surface-container-highest hover:text-primary transition-none border-b border-outline-variant"
              >
                CLEAR FEED
              </button>
              <button 
                onClick={() => { alert('Log export requested'); setShowFeedMenu(false); }} 
                className="px-4 py-3 text-left font-label-caps text-[10px] text-on-surface hover:bg-surface-container-highest transition-none border-b border-outline-variant"
              >
                EXPORT LOGS
              </button>
              <button 
                onClick={() => setShowFeedMenu(false)} 
                className="px-4 py-3 text-left font-label-caps text-[10px] text-error hover:bg-[#2d1212] transition-none"
              >
                MUTE ALERTS
              </button>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {(() => {
            const filteredLogs = agentLog.filter(log => feedFilter === 'ALL' || log.severity === 'ERROR' || log.severity === 'CRITICAL');
            
            if (filteredLogs.length === 0) {
              return (
                <div className="text-center font-data-tabular text-[12px] text-on-surface-variant mt-10">
                  {feedFilter === 'ALERTS' ? 'No alerts available' : 'No logs available'}
                </div>
              );
            }

            return filteredLogs.map((log) => {
              const time = new Date(log.logged_at).toLocaleTimeString('en-US', { hour12: true, timeZone: 'Asia/Kolkata' }) + ' IST';
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
            });
          })()}
        </div>
        </aside>
      )}
    </>
  );
}
