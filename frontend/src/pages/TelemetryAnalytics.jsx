import React, { useState, useEffect } from 'react';
import { CalendarDays, Download } from 'lucide-react';
import API_CONFIG from '../api';

const API_BASE = `${API_CONFIG}/api/monitor`;

export default function TelemetryAnalytics() {
  const [nationalTrend, setNationalTrend] = useState(null);

  useEffect(() => {
    const fetchStatus = () => {
      fetch(`${API_BASE}/status`)
        .then(r => r.json())
        .then(d => {
          if (d?.national_trend) {
            setNationalTrend(d.national_trend);
          }
        })
        .catch(console.error);
    };
    
    fetchStatus();
    const id = setInterval(fetchStatus, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="w-full h-screen overflow-y-auto pt-10 px-8 pb-20 bg-background text-on-background font-body-md selection:bg-primary selection:text-on-primary">
      <div className="max-w-[1600px] mx-auto flex flex-col gap-container-margin">
        {/* Page Header */}
        <div className="flex justify-between items-end border-b border-outline-variant pb-4">
          <div>
            <h2 className="font-headline-md text-[24px] font-bold text-primary mb-1">TELEMETRY: 30-DAY TRENDS</h2>
            <p className="font-body-md text-[14px] text-on-surface-variant">Global probabilistic models and localized atmospheric saturation.</p>
          </div>
          <div className="flex gap-2">
            <button className="bg-surface text-on-surface border border-outline-variant px-4 h-[32px] font-label-caps text-[11px] flex items-center gap-2 hover:bg-surface-container-highest transition-none">
              <CalendarDays size={16} />
              T-30 TO T-0
            </button>
            <button className="bg-primary text-on-primary border border-primary px-4 h-[32px] font-label-caps text-[11px] flex items-center gap-2 transition-none hover:bg-surface-tint">
              <Download size={16} />
              EXPORT
            </button>
          </div>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-12 gap-[1px] bg-outline-variant border border-outline-variant">
          
          {/* Widget 1: Historical Flood Probabilities (Line Chart) */}
          <div className="col-span-12 xl:col-span-8 bg-background flex flex-col relative h-[400px]">
            <div className="absolute inset-0 grid-blueprint opacity-20 pointer-events-none"></div>
            
            <div className="flex justify-between items-center p-4 border-b border-outline-variant bg-surface-container-lowest z-10">
              <h3 className="font-label-caps text-[11px] text-on-surface">NATIONAL AVERAGE FLOOD PROBABILITY (%)</h3>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-0.5 bg-primary"></div>
                  <span className="font-data-tabular text-[11px] text-on-surface-variant">ACTUAL</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-0.5 bg-error"></div>
                  <span className="font-data-tabular text-[11px] text-on-surface-variant">THRESHOLD</span>
                </div>
              </div>
            </div>

            <div className="flex-1 p-4 flex z-10 relative">
              {/* Y Axis Labels */}
              <div className="flex flex-col justify-between items-end pr-4 border-r border-outline-variant font-data-tabular text-[11px] text-on-surface-variant h-full pb-6">
                <span>100</span>
                <span>75</span>
                <span>50</span>
                <span>25</span>
                <span>0</span>
              </div>
              
              {/* Chart Area */}
              <div className="flex-1 relative w-full h-full pl-4">
                <svg className="w-full h-[calc(100%-24px)] overflow-visible" preserveAspectRatio="none" viewBox="0 0 1000 300">
                  {/* Horizontal Grid Lines */}
                  <line className="text-outline-variant opacity-50" stroke="currentColor" strokeWidth="1" x1="0" x2="1000" y1="0" y2="0"></line>
                  <line className="text-outline-variant opacity-50" stroke="currentColor" strokeWidth="1" x1="0" x2="1000" y1="75" y2="75"></line>
                  <line className="text-outline-variant opacity-50" stroke="currentColor" strokeWidth="1" x1="0" x2="1000" y1="150" y2="150"></line>
                  <line className="text-outline-variant opacity-50" stroke="currentColor" strokeWidth="1" x1="0" x2="1000" y1="225" y2="225"></line>
                  <line className="text-outline-variant opacity-50" stroke="currentColor" strokeWidth="1" x1="0" x2="1000" y1="300" y2="300"></line>

                  {/* Threshold Line */}
                  <line className="text-error opacity-80" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" x1="0" x2="1000" y1="60" y2="60"></line>

                  {/* Data Line */}
                  <polyline 
                    className="text-primary" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    points="0,280 100,290 200,270 300,290 400,260 500,280 600,250 700,260 800,210 900,220 1000,180" 
                  />
                  {nationalTrend && (
                    <polyline 
                      className="text-error" 
                      fill="none" 
                      stroke="currentColor" 
                      strokeWidth="2" 
                      points={`900,220 1000,${300 - (nationalTrend * 300)}`} 
                    />
                  )}
                  
                  {/* Data Points */}
                  <circle className="text-primary fill-background" cx="800" cy="210" r="3" stroke="currentColor" strokeWidth="1"></circle>
                  <circle className="text-primary fill-background" cx="900" cy="220" r="3" stroke="currentColor" strokeWidth="1"></circle>
                  <circle className="text-primary fill-primary" cx="1000" cy={nationalTrend ? 300 - (nationalTrend * 300) : 180} r="4" stroke="currentColor" strokeWidth="1"></circle>
                </svg>

                {/* X Axis Labels */}
                <div className="absolute bottom-0 left-4 right-0 flex justify-between font-data-tabular text-[11px] text-on-surface-variant">
                  <span>T-30</span>
                  <span>T-20</span>
                  <span>T-10</span>
                  <span>T-0</span>
                </div>
              </div>
            </div>
          </div>

          {/* Widget 2: Threat Distribution */}
          <div className="col-span-12 xl:col-span-4 bg-background flex flex-col h-[400px]">
            <div className="p-4 border-b border-outline-variant bg-surface-container-lowest">
              <h3 className="font-label-caps text-[11px] text-on-surface">THREAT SEVERITY DISTRIBUTION</h3>
            </div>
            <div className="flex-1 p-6 flex flex-col justify-center gap-6">
              <div className="flex flex-col gap-2">
                <div className="flex justify-between font-data-tabular text-[11px] text-on-surface">
                  <span>CRITICAL</span>
                  <span className="text-error">12%</span>
                </div>
                <div className="w-full h-1 bg-surface-container-highest">
                  <div className="h-full bg-error" style={{ width: '12%' }}></div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex justify-between font-data-tabular text-[11px] text-on-surface">
                  <span>HIGH</span>
                  <span>24%</span>
                </div>
                <div className="w-full h-1 bg-surface-container-highest">
                  <div className="h-full bg-primary" style={{ width: '24%' }}></div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex justify-between font-data-tabular text-[11px] text-on-surface">
                  <span>MODERATE</span>
                  <span className="text-on-surface-variant">64%</span>
                </div>
                <div className="w-full h-1 bg-surface-container-highest">
                  <div className="h-full bg-outline-variant" style={{ width: '64%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
