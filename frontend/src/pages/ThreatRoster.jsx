import React, { useState, useEffect } from 'react';
import { Filter, Download, ChevronDown } from 'lucide-react';
import API_CONFIG from '../api';

const API_BASE = `${API_CONFIG}/api/monitor`;

export default function ThreatRoster() {
  const [threats, setThreats] = useState([]);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    const fetchThreats = () => {
      fetch(`${API_BASE}/threats`)
        .then(r => r.json())
        .then(d => setThreats(Array.isArray(d) ? d : []))
        .catch(console.error);
    };
    
    fetchThreats();
    const id = setInterval(fetchThreats, 5000);
    return () => clearInterval(id);
  }, []);

  const toggleExpand = (id) => {
    if (expandedRow === id) {
      setExpandedRow(null);
    } else {
      setExpandedRow(id);
    }
  };

  return (
    <div className="w-full h-screen overflow-y-auto pt-10 px-8 pb-20 bg-background text-on-background font-body-md selection:bg-primary selection:text-on-primary">
      <div className="max-w-[1600px] mx-auto">
        {/* Page Header */}
        <div className="flex justify-between items-end mb-6 border-b border-outline-variant pb-4">
          <div>
            <h1 className="font-headline-lg text-[32px] font-bold text-primary tracking-tighter">ACTIVE ANOMALIES</h1>
            <p className="font-data-tabular text-[13px] text-on-surface-variant mt-1">QUERY: GLOBAL // STATUS: FILTERED_ROSTER // RECORDS: {threats.length}</p>
          </div>
          <div className="flex gap-2">
            <button className="bg-surface-container-highest text-on-surface font-label-caps text-[11px] px-4 py-2 border border-outline-variant hover:bg-surface-bright transition-none flex items-center gap-2">
              <Filter size={16} /> FILTER
            </button>
            <button className="bg-primary text-on-primary font-label-caps text-[11px] px-4 py-2 border border-primary hover:bg-surface-tint transition-none flex items-center gap-2">
              <Download size={16} /> EXPORT
            </button>
          </div>
        </div>

        {/* Data Table Structure */}
        <div className="w-full border border-outline-variant bg-surface mb-12">
          {/* Table Header */}
          <div className="bg-surface-container-high border-b border-outline-variant px-4 min-h-[40px] flex items-center">
            <div className="threat-grid w-full font-label-caps text-[11px] text-on-surface-variant">
              <div>SECTOR_ID</div>
              <div>REGION</div>
              <div>RISK_LEVEL</div>
              <div>FLD_PROB(%)</div>
              <div className="hide-tablet">24H_RAIN(MM)</div>
              <div className="text-right">STATUS</div>
            </div>
          </div>

          {/* Table Body */}
          <div className="flex flex-col">
            {threats.length === 0 ? (
              <div className="p-8 text-center text-on-surface-variant font-data-tabular">NO ACTIVE ANOMALIES DETECTED</div>
            ) : (
              threats.map((threat) => {
                const isCritical = threat.risk_level === 'CRITICAL';
                const isExpanded = expandedRow === threat.id;
                
                let rowBgClass = isCritical ? 'bg-error-container/20 border-l-[3px] border-l-error' : 'bg-surface border-l-[3px] border-l-transparent';
                
                return (
                  <div key={threat.id} className={`border-b border-outline-variant group ${isExpanded ? 'expanded' : ''}`}>
                    {/* Primary Row Data */}
                    <div 
                      className={`${rowBgClass} px-4 min-h-[48px] cursor-pointer hover:bg-surface-container-highest transition-none flex items-center`}
                      onClick={() => toggleExpand(threat.id)}
                    >
                      <div className="threat-grid w-full font-data-tabular text-[13px] text-primary">
                        <div>{threat.cell_id}</div>
                        <div className="truncate">{threat.cell_name}</div>
                        <div>
                          <span className={`${isCritical ? 'bg-error text-on-error border-error' : 'bg-surface-container-highest text-on-surface border-outline-variant'} font-label-caps px-2 py-1 border inline-block`}>
                            {threat.risk_level}
                          </span>
                        </div>
                        <div className={isCritical ? "text-error font-bold" : ""}>
                          {(threat.flood_prob * 100).toFixed(1)}%
                        </div>
                        <div className="hide-tablet">{threat.rainfall_d1 ? threat.rainfall_d1.toFixed(1) : "0.0"}</div>
                        <div className="text-right flex items-center justify-end gap-2 text-on-surface-variant">
                          <span className={`w-2 h-2 ${isCritical ? 'bg-error animate-ping' : 'bg-primary'} rounded-none`}></span>
                          ACTIVE
                          <ChevronDown size={16} className={`transition-transform duration-0 ${isExpanded ? 'rotate-180' : ''}`} />
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details Panel */}
                    {isExpanded && (
                      <div className="bg-surface-container p-6 border-t border-outline-variant font-data-tabular text-[13px] text-on-surface">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                          <div>
                            <h4 className="font-label-caps text-[11px] text-on-surface-variant mb-4 border-b border-outline-variant pb-2">AI RESPONSE PLAN // SITREP</h4>
                            <ul className="space-y-2 text-primary">
                              {isCritical && <li>&gt; <span className="text-error">IMMEDIATE ACTION REQUIRED</span></li>}
                              <li>&gt; INIT EXTRAC PROTOCOL 4-B</li>
                              <li>&gt; MOBILIZE ASSETS: TR-9, TR-14</li>
                              <li>&gt; EST. IMPACT TIME: T-MINUS 04:22:00</li>
                              <li>&gt; <strong>SYS_NOTE:</strong> {threat.ai_summary || "Awaiting advanced deep scan telemetry."}</li>
                            </ul>
                          </div>
                          <div>
                            <h4 className="font-label-caps text-[11px] text-on-surface-variant mb-4 border-b border-outline-variant pb-2">RAW TELEMETRY DUMP</h4>
                            <div className="bg-surface-container-lowest border border-outline-variant p-3 overflow-x-auto text-on-surface-variant text-[11px] font-data-tabular">
                              <code>
                                {JSON.stringify({
                                  lat: threat.lat,
                                  lon: threat.lon,
                                  risk_score: threat.risk_score,
                                  trend: threat.trend,
                                  hotspots: threat.hotspot_count
                                }, null, 2)}
                              </code>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
