import React, { useState, useEffect } from 'react';
import { Radar, Check, AlertTriangle } from 'lucide-react';
import API_CONFIG from '../api';

const API_BASE = `${API_CONFIG}/api/monitor`;

export default function SystemConfiguration() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  
  const handleTriggerScan = async () => {
    if (isScanning) return;
    setIsScanning(true);
    setScanResult(null);
    try {
      const res = await fetch(`${API_BASE}/scan`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setScanResult({ success: true, message: data.message || 'Scan completed successfully.' });
    } catch (err) {
      console.error('Scan trigger failed:', err);
      setScanResult({ success: false, message: 'Scan failed. See console for details.' });
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="w-full h-screen overflow-y-auto pt-10 px-8 pb-20 bg-background text-on-background font-body-md selection:bg-primary selection:text-on-primary">
      <div className="max-w-[1600px] mx-auto flex flex-col gap-6">
        
        {/* Page Header */}
        <div className="border-b border-outline-variant pb-4">
          <h1 className="font-headline-lg text-[32px] font-bold text-on-background tracking-tighter">SYSTEM CONFIGURATION</h1>
          <p className="font-body-md text-[14px] text-on-surface-variant mt-2 max-w-2xl">Modify core operational parameters, external data ingress tokens, and manual override protocols. Changes are logged immutably.</p>
        </div>

        {/* Settings Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
          
          {/* Column 1: Alerting & Integrations */}
          <div className="flex flex-col gap-6">
            
            {/* Alerting Panel */}
            <section className="bg-surface-container-low border border-outline-variant p-6">
              <header className="border-b border-outline-variant pb-3 mb-6">
                <h2 className="font-label-caps text-[11px] text-on-surface">COMMUNICATIONS PROTOCOL</h2>
              </header>
              <div className="flex flex-col gap-6">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h3 className="font-body-lg text-[16px] text-on-background">Autonomous Telegram Alerting</h3>
                    <p className="font-body-md text-[14px] text-on-surface-variant mt-1">Deploy automated sitreps to assigned field operatives upon threshold breach.</p>
                  </div>
                  <label className="brutal-toggle mt-1 shrink-0">
                    <input type="checkbox" defaultChecked />
                    <span className="track"><span className="thumb"></span></span>
                  </label>
                </div>
                
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h3 className="font-body-lg text-[16px] text-on-background">Strict Payload Formatting</h3>
                    <p className="font-body-md text-[14px] text-on-surface-variant mt-1">Force JSON strict mode on all outbound webhook transmissions.</p>
                  </div>
                  <label className="brutal-toggle mt-1 shrink-0">
                    <input type="checkbox" />
                    <span className="track"><span className="thumb"></span></span>
                  </label>
                </div>
              </div>
            </section>

            {/* API Keys Panel */}
            <section className="bg-surface-container-low border border-outline-variant p-6">
              <header className="border-b border-outline-variant pb-3 mb-6">
                <h2 className="font-label-caps text-[11px] text-on-surface">EXTERNAL DATA INGRESS (API)</h2>
              </header>
              <div className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                  <label className="font-label-caps text-[11px] text-on-surface-variant flex justify-between">
                    <span>NASA FIRMS ENDPOINT KEY</span>
                    <span className="text-secondary">ACTIVE</span>
                  </label>
                  <input 
                    className="bg-surface border border-outline-variant text-on-background font-data-tabular text-[13px] p-3 focus:border-primary focus:ring-0 focus:outline-none placeholder:text-on-surface-variant w-full" 
                    readOnly 
                    type="text" 
                    value="NF-88392-XX-91A-BETA" 
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="font-label-caps text-[11px] text-on-surface-variant flex justify-between">
                    <span>OPEN-METEO SYNC TOKEN</span>
                    <span className="text-on-surface-variant">MODIFIABLE</span>
                  </label>
                  <div className="flex gap-2 relative group">
                    <input 
                      className="bg-surface border border-outline-variant text-on-background font-data-tabular text-[13px] p-3 focus:border-primary focus:ring-0 focus:outline-none placeholder:text-on-surface-variant w-full" 
                      placeholder="Enter Token" 
                      type="password" 
                      defaultValue="OM-TRK-9921-ALPHA-SIGMA" 
                    />
                    <button className="border border-outline-variant bg-surface hover:bg-surface-container-highest px-4 font-label-caps text-[11px] text-on-surface transition-none h-full absolute right-0 top-0 border-l-0">
                      UPDATE
                    </button>
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* Column 2: System Overrides & Info */}
          <div className="flex flex-col gap-6">
            
            {/* Override Panel */}
            <section className="bg-[#1a0505] border border-error p-6 relative overflow-hidden">
              {/* Hazard Striping Top */}
              <div 
                className="absolute top-0 left-0 w-full h-1" 
                style={{ background: "repeating-linear-gradient(45deg, #ffb4ab, #ffb4ab 10px, transparent 10px, transparent 20px)" }}>
              </div>
              
              <header className="border-b border-error pb-3 mb-6 flex items-center gap-2">
                <AlertTriangle className="text-error" size={20} />
                <h2 className="font-label-caps text-[11px] text-error">CRITICAL OVERRIDES</h2>
              </header>
              
              <div className="flex flex-col gap-6">
                <div>
                  <h3 className="font-body-lg text-[16px] text-on-background">Force National Scan</h3>
                  <p className="font-body-md text-[14px] text-on-surface-variant mt-2 max-w-md">
                    Manually triggers a full-spectrum telemetry sweep across all deployed nodes. Bypasses standard queuing protocols and incurs high compute latency.
                  </p>
                </div>
                
                <button 
                  onClick={handleTriggerScan}
                  disabled={isScanning}
                  className={`font-label-caps text-[11px] px-6 py-4 flex items-center justify-center gap-3 w-fit transition-none border ${
                    isScanning 
                      ? 'bg-surface-container-highest text-on-surface border-outline-variant cursor-wait' 
                      : 'bg-primary text-on-primary border-primary hover:bg-surface-container-highest hover:text-primary'
                  }`}
                >
                  <Radar size={18} className={isScanning ? 'animate-spin' : ''} />
                  {isScanning ? 'SCAN IN PROGRESS...' : 'EXECUTE NATIONAL SCAN'}
                </button>
                
                {scanResult && (
                  <div className={`mt-2 font-data-tabular text-[11px] flex items-center gap-2 ${scanResult.success ? 'text-primary' : 'text-error'}`}>
                    {scanResult.success ? <Check size={14} /> : <AlertTriangle size={14} />}
                    {scanResult.message}
                  </div>
                )}
              </div>
            </section>

            {/* System Telemetry Readout */}
            <section className="bg-surface border border-outline-variant p-6">
              <header className="border-b border-outline-variant pb-3 mb-4">
                <h2 className="font-label-caps text-[11px] text-on-surface">LOCAL NODE TELEMETRY</h2>
              </header>
              <div className="font-data-tabular text-[13px] text-on-surface-variant flex flex-col gap-2">
                <div className="flex justify-between border-b border-surface-container-highest pb-1">
                  <span>UPTIME</span>
                  <span className="text-on-background">14d 08h 22m</span>
                </div>
                <div className="flex justify-between border-b border-surface-container-highest pb-1">
                  <span>LAST SYNC</span>
                  <span className="text-on-background">{new Date().toISOString().replace('T', ' ').substring(0, 19)} UTC</span>
                </div>
                <div className="flex justify-between border-b border-surface-container-highest pb-1">
                  <span>MEMORY ALLOC</span>
                  <span className="text-on-background">84% (4.2GB / 5.0GB)</span>
                </div>
                <div className="flex justify-between pb-1">
                  <span>DB VERSION</span>
                  <span className="text-on-background">v9.1.4-brutal</span>
                </div>
              </div>
            </section>
          </div>

        </div>
      </div>
    </div>
  );
}
