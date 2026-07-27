import React, { useState, useEffect } from 'react';
import { X, Download, ChevronRight, Activity, Satellite, Layers, MapPin } from 'lucide-react';
import API_CONFIG from '../api';

export default function CellDetailPanel({ cell, riskLevel, onClose }) {
  const [satTrue, setSatTrue] = useState(null);
  const [satFalse, setSatFalse] = useState(null);
  const [loadingGee, setLoadingGee] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (!cell) return;
    setLoadingGee(true);
    
    // Fetch GEE Satellite Data
    fetch(`${API_CONFIG}/api/cell/${cell.cell_id}/gee`)
      .then(r => r.json())
      .then(data => {
        if (data.satellite?.true_color) setSatTrue(data.satellite.true_color);
        if (data.satellite?.false_color) setSatFalse(data.satellite.false_color);
      })
      .catch(console.error)
      .finally(() => setLoadingGee(false));

    // Fetch Cell Telemetry History
    fetch(`${API_CONFIG}/api/monitor/cell/${cell.cell_id}`)
      .then(r => r.json())
      .then(data => {
        setHistory(data || []);
      })
      .catch(console.error);

  }, [cell]);

  if (!cell) return null;

  const isCritical = riskLevel === 'CRITICAL';
  const isHigh = riskLevel === 'HIGH';
  const isWarning = isCritical || isHigh;

  const latest = history[0] || {};
  const scannedAt = latest.scanned_at 
    ? new Date(latest.scanned_at).toLocaleTimeString('en-US', { hour12: true, timeZone: 'Asia/Kolkata' }) + ' IST' 
    : 'UNKNOWN';

  const floodPct = latest.flood_prob != null 
    ? (latest.flood_prob === 0 ? '0.0%' : latest.flood_prob < 0.001 ? '<0.1%' : `${(latest.flood_prob * 100).toFixed(1)}%`)
    : 'N/A';

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const res = await fetch(`${API_CONFIG}/api/report/generate/${cell.cell_id}`);
      if (!res.ok) throw new Error('Failed to generate report');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SITREP_${cell.cell_id}.pdf`;
      a.click();
    } catch (e) {
      console.error(e);
      alert('Failed to generate report');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <aside className="flex-[3] min-w-[320px] max-w-[480px] bg-surface-container border-l border-outline-variant flex flex-col h-full z-20 overflow-hidden">
      {/* Header */}
      <header className={`h-12 border-b border-outline-variant flex items-center justify-between px-4 flex-shrink-0 ${isWarning ? 'bg-[#2d1212]' : 'bg-surface-container-lowest'}`}>
        <div className="flex items-center gap-2">
          <Activity className={isWarning ? 'text-error' : 'text-primary'} size={18} />
          <h2 className={`font-label-caps text-[11px] tracking-widest ${isWarning ? 'text-error' : 'text-primary'}`}>TACTICAL READOUT</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1 font-data-tabular text-[10px] border px-1 ${isWarning ? 'border-error text-error bg-error-container' : 'border-outline-variant text-on-surface-variant bg-surface-container'}`}>
            <span className={`w-1.5 h-1.5 block rounded-none ${isWarning ? 'bg-error' : 'bg-secondary-container'}`}></span>
            {riskLevel || 'SECURE'}
          </div>
          <button onClick={onClose} className="text-on-surface-variant hover:text-on-surface transition-none">
            <X size={16} />
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6">
        
        {/* Title Block */}
        <div>
          <h3 className="font-headline-md text-on-background">{cell.name}</h3>
          <div className="font-data-tabular text-[11px] text-on-surface-variant flex items-center gap-1 mt-1 uppercase">
            <MapPin size={12} /> {cell.state} | {cell.cell_id}
          </div>
        </div>

        {/* Core Telemetry Grid */}
        <section className="bg-surface border border-outline-variant">
          <header className="border-b border-outline-variant px-3 py-2 bg-surface-container-low font-label-caps text-[10px] text-on-surface flex items-center gap-2">
            <Layers size={12} /> CURRENT STATUS
          </header>
          <div className="grid grid-cols-2 gap-px bg-outline-variant">
            <MetricBox label="Flood Prob" value={floodPct} isAlert={isWarning} />
            <MetricBox label="Hotspots" value={latest.hotspots ?? 'NONE'} />
            <MetricBox label="Rainfall (24h)" value={latest.rainfall_d1 != null ? `${latest.rainfall_d1.toFixed(1)}mm` : '—'} />
            <MetricBox label="Last Sync" value={scannedAt} />
          </div>
        </section>

        {/* Sentinel Imagery */}
        <section className="bg-surface border border-outline-variant">
          <header className="border-b border-outline-variant px-3 py-2 bg-surface-container-low font-label-caps text-[10px] text-on-surface flex items-center gap-2">
            <Satellite size={12} /> SATELLITE IMAGERY (SENTINEL/MODIS)
          </header>
          <div className="p-3 bg-surface">
            {loadingGee ? (
              <div className="h-32 border border-outline-variant flex items-center justify-center font-data-tabular text-[11px] text-on-surface-variant animate-pulse bg-surface-container-low">
                INITIALIZING SAT-LINK...
              </div>
            ) : satTrue ? (
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <img src={satTrue} alt="True Color" className="w-full aspect-square object-cover border border-outline-variant" onError={e => e.target.style.display='none'} />
                  <span className="font-data-tabular text-[9px] text-on-surface-variant">RGB / NATURAL</span>
                </div>
                <div className="flex flex-col gap-1">
                  <img src={satFalse || satTrue} alt="False Color" className="w-full aspect-square object-cover border border-outline-variant" onError={e => e.target.style.display='none'} />
                  <span className="font-data-tabular text-[9px] text-on-surface-variant">NIR / ENHANCED</span>
                </div>
              </div>
            ) : (
              <div className="h-24 border border-outline-variant flex items-center justify-center font-data-tabular text-[11px] text-on-surface-variant bg-surface-container-low">
                IMAGERY UNAVAILABLE
              </div>
            )}
          </div>
        </section>

        {/* Regional Context */}
        <section className="bg-surface border border-outline-variant">
          <header className="border-b border-outline-variant px-3 py-2 bg-surface-container-low font-label-caps text-[10px] text-on-surface">
            REGIONAL CONTEXT
          </header>
          <div className="flex flex-col text-[11px] font-data-tabular">
            <div className="flex justify-between border-b border-outline-variant px-3 py-2">
              <span className="text-on-surface-variant">COORDINATES</span>
              <span className="text-on-surface">{cell.lat.toFixed(4)}°N, {cell.lon.toFixed(4)}°E</span>
            </div>
            <div className="flex justify-between border-b border-outline-variant px-3 py-2">
              <span className="text-on-surface-variant">POP DENSITY</span>
              <span className="text-on-surface">{cell.population_density} / KM²</span>
            </div>
            <div className="flex justify-between px-3 py-2">
              <span className="text-on-surface-variant">HAZARDS</span>
              <span className="text-on-surface uppercase">{cell.risk_profile?.join(', ').replace(/_/g, ' ') || 'NONE'}</span>
            </div>
          </div>
        </section>
      </div>

      {/* Actions */}
      <div className="flex gap-2 p-4 border-t border-outline-variant bg-surface-container flex-shrink-0">
        <button 
          className="flex-1 bg-primary text-on-primary font-label-caps text-[11px] py-3 flex justify-center items-center gap-2 hover:bg-surface-bright transition-none border border-primary"
          onClick={() => alert("Response Plan interface not implemented yet.")}
        >
          VIEW SITREP
          <ChevronRight size={14} />
        </button>
        
        <button 
          onClick={handleDownloadPDF} 
          disabled={downloading}
          className={`flex-1 font-label-caps text-[11px] py-3 flex justify-center items-center gap-2 border transition-none ${downloading ? 'bg-surface-container-highest border-outline-variant text-on-surface-variant' : 'bg-surface text-on-surface border-outline-variant hover:bg-surface-container-highest hover:text-primary'}`}
        >
          <Download size={14} />
          {downloading ? 'GENERATING...' : 'EXPORT PDF'}
        </button>
      </div>
    </aside>
  );
}

function MetricBox({ label, value, isAlert }) {
  return (
    <div className={`bg-surface p-3 flex flex-col gap-1 ${isAlert ? 'bg-[#1a0505]' : ''}`}>
      <span className="font-label-caps text-[9px] text-on-surface-variant">{label}</span>
      <span className={`font-data-tabular text-[16px] ${isAlert ? 'text-error' : 'text-on-surface'}`}>{value}</span>
    </div>
  );
}
