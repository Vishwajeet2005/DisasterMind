import React, { useState, useEffect } from 'react';
import { Download, X, MapPin, AlertCircle, Image as ImageIcon, ChevronRight } from 'lucide-react';
import ResponsePlanPanel from './ResponsePlanPanel';
import API_CONFIG from '../api';

const API_BASE = API_CONFIG;

const RISK_CONFIG = {
  CRITICAL: { color: 'var(--risk-critical-color)', bg: 'var(--risk-critical-bg)', border: 'var(--risk-critical-border)' },
  HIGH:     { color: 'var(--risk-high-color)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)' },
  MODERATE: { color: 'var(--risk-moderate-color)', bg: 'var(--risk-moderate-bg)', border: 'var(--risk-moderate-border)' },
  LOW:      { color: 'var(--risk-low-color)',      bg: 'var(--risk-low-bg)',      border: 'var(--risk-low-border)' },
};

export default function CellDetailPanel({ cell, riskLevel, onClose }) {
  const [history,    setHistory]    = useState([]);
  const [geeData,    setGeeData]    = useState(null);
  const [loadingGee, setLoadingGee] = useState(false);
  const [downloading, setDL]        = useState(false);
  const [showPlan,   setShowPlan]   = useState(false);

  useEffect(() => {
    if (!cell?.cell_id) return;
    fetch(`${API_BASE}/api/monitor/cell/${cell.cell_id}`)
      .then(r => r.json()).then(setHistory).catch(() => {});

    setLoadingGee(true);
    setGeeData(null);
    fetch(`${API_BASE}/api/cell/${cell.cell_id}/gee`)
      .then(r => r.json())
      .then(d => { setGeeData(d); setLoadingGee(false); })
      .catch(() => setLoadingGee(false));
  }, [cell?.cell_id]);

  const rc     = RISK_CONFIG[riskLevel] || RISK_CONFIG.LOW;
  const latest = history[0] || {};
  let raw = {};
  try { raw = latest.raw_json ? JSON.parse(latest.raw_json) : {}; } catch {}

  const floodPct  = latest.flood_prob != null ? `${(latest.flood_prob * 100).toFixed(0)}%` : '—';
  const scannedAt = latest.scanned_at
    ? new Date(latest.scanned_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
    : 'Pending Data';

  const handleDownloadPDF = async () => {
    setDL(true);
    try {
      const riskLvl   = riskLevel || 'LOW';
      const floodProb = latest?.flood_prob ?? 0;
      const riskScore = latest?.risk_score ?? 1;
      const popMin    = Math.round((cell.population_density || 50) * 625 / 1000);
      const popMax    = Math.round((cell.population_density || 50) * 625 * 2 / 1000);

      const analysis = {
        region: `${cell.name}, ${cell.state}`,
        timestamp: latest?.scanned_at || new Date().toISOString(),
        coordinates: { lat: cell.lat, lon: cell.lon },
        situation_report: {
          risk_level: riskLvl,
          risk_score: riskScore,
          situation_summary: `System scan identified ${riskLvl} risk in ${cell.name}, ${cell.state}. Flood probability: ${(floodProb * 100).toFixed(0)}%. Active FIRMS hotspots: ${latest?.hotspots ?? 0}. Day-1 rainfall forecast: ${(latest?.rainfall_d1 ?? 0).toFixed(0)}mm. Population density: ${cell.population_density}/km². Immediate assessment recommended.`,
          primary_threat: (cell.risk_profile?.[0] || 'flood').toUpperCase(),
          estimated_affected_population: `${popMin}K–${popMax}K`,
          priority_zones: [],
          resources_required: {
            ndrf_teams:       riskLvl === 'CRITICAL' ? 5 : riskLvl === 'HIGH' ? 3 : 2,
            rescue_boats:     riskLvl === 'CRITICAL' ? 12 : riskLvl === 'HIGH' ? 8 : 4,
            helicopters:      riskLvl === 'CRITICAL' ? 3 : 1,
            medical_units:    riskLvl === 'CRITICAL' ? 6 : riskLvl === 'HIGH' ? 4 : 2,
            evacuation_buses: riskLvl === 'CRITICAL' ? 20 : riskLvl === 'HIGH' ? 12 : 6,
            water_tankers:    riskLvl === 'CRITICAL' ? 10 : 5,
          },
          action_timeline: [
            { hour: '0–6 hrs',   action: 'Deploy advance team. Activate District EOC. Alert hospitals within 50km.' },
            { hour: '6–12 hrs',  action: 'Begin evacuation of high-risk zones. Deploy rescue boats. Establish relief camps.' },
            { hour: '12–24 hrs', action: 'Full resource mobilisation. Coordinate with SDMA. Initiate food and medicine supply chain.' },
            { hour: '24–48 hrs', action: 'Damage assessment in cleared zones. Continue search and rescue. Restore communication.' },
          ],
          evacuation_recommendation: riskLvl === 'CRITICAL' ? 'MANDATORY' : riskLvl === 'HIGH' ? 'ADVISORY' : 'STANDBY',
          escalation_risk: riskLvl === 'CRITICAL' ? 'Situation may deteriorate rapidly. Multi-district coordination required.' : '',
          coordination_agencies: ['NDMA', 'SDMA', 'District Collector', 'Indian Army', 'Coast Guard'],
          key_roads_status: 'Assessment in progress — verify NH connectivity before deploying convoys.',
        },
        ml_prediction: {
          flood_probability: floodProb,
          severity_label:    latest?.severity || riskLvl,
          ml_confidence:     riskScore >= 7 ? 'HIGH' : riskScore >= 4 ? 'MEDIUM' : 'LOW',
        },
        raw_data:    raw || {},
        data_sources: ['NASA FIRMS VIIRS', 'Open-Meteo', 'OpenTopoData', 'System Models'],
        processing_time_ms: 0,
      };

      const res = await fetch(`${API_BASE}/report/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `DisasterMind_${cell.name.replace(/[,\s]+/g, '_')}_Report.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('PDF download failed: ' + e.message);
    } finally {
      setDL(false);
    }
  };

  const satTrue  = geeData?.satellite?.true_color  || raw?.satellite?.true_color;
  const satFalse = geeData?.satellite?.false_color || raw?.satellite?.false_color;

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

        {/* ── Header ─────────────────────────────────────────────── */}
        <div style={{
          padding: '24px',
          borderBottom: 'var(--border-subtle)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 20, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em', marginBottom: 4 }}>
                {cell.name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <MapPin size={14} color="var(--text-secondary)" />
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  {cell.state}
                </span>
              </div>
            </div>
            <button onClick={onClose} style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              padding: 4,
            }}>
              <X size={20} />
            </button>
          </div>

          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '6px 12px',
            background: rc.bg,
            border: `1px solid ${rc.border}`,
            borderRadius: 'var(--radius-sm)',
          }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: rc.color }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: rc.color }}>
              {riskLevel || 'LOW'} Risk
            </span>
          </div>
        </div>

        {/* ── Scrollable Body ───────────────────────────────────── */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>

          {/* ── Key Metrics ─────────────────────────────────────── */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              Current Status
            </div>
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16,
            }}>
              <MetricCard label="Flood Probability" value={floodPct} />
              <MetricCard label="Active Hotspots" value={latest.hotspots ?? 'None'} />
              <MetricCard label="Rainfall (24h)" value={latest.rainfall_d1 != null ? `${latest.rainfall_d1.toFixed(1)} mm` : '—'} />
              <MetricCard label="Last Updated" value={scannedAt} />
            </div>
          </div>

          {/* ── Satellite Imagery ────────────────────────────────── */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                Satellite Imagery
              </div>
            </div>

            {loadingGee ? (
              <div style={{
                height: 120, borderRadius: 'var(--radius-md)',
                background: 'var(--bg-glass-hover)',
                border: 'var(--border-subtle)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, color: 'var(--text-secondary)',
              }}>
                Loading imagery...
              </div>
            ) : satTrue ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <img src={satTrue} alt="True Color" style={{
                    width: '100%', aspectRatio: '1', objectFit: 'cover',
                    borderRadius: 'var(--radius-md)', border: 'var(--border-subtle)',
                  }} onError={e => e.target.style.display='none'} />
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>Natural Color</div>
                </div>
                <div>
                  <img src={satFalse || satTrue} alt="False Color" style={{
                    width: '100%', aspectRatio: '1', objectFit: 'cover',
                    borderRadius: 'var(--radius-md)', border: 'var(--border-subtle)',
                  }} onError={e => e.target.style.display='none'} />
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>Enhanced (Water/Veg)</div>
                </div>
              </div>
            ) : (
              <div style={{
                height: 100, borderRadius: 'var(--radius-md)',
                background: 'var(--bg-glass-hover)',
                border: 'var(--border-subtle)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, color: 'var(--text-secondary)',
              }}>
                Imagery unavailable
              </div>
            )}
          </div>

          {/* ── Regional Context ──────────────────────────────────── */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              Regional Context
            </div>
            <div style={{
              background: 'var(--bg-glass-hover)',
              border: 'var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
            }}>
              <ContextRow label="Grid Reference" value={`${cell.lat.toFixed(3)}°N, ${cell.lon.toFixed(3)}°E`} mono />
              <ContextRow label="Population Density" value={`${cell.population_density} / km²`} />
              <ContextRow label="Primary Hazards" value={cell.risk_profile?.join(', ').replace(/_/g, ' ') || 'None'} capitalize />
            </div>
          </div>

          {/* ── Actions ─────────────────────────────────────────── */}
          <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
            <button onClick={() => setShowPlan(true)} style={{
              flex: 1, padding: '12px 16px',
              background: 'var(--text-primary)',
              color: '#000',
              border: 'none',
              borderRadius: 'var(--radius-md)', cursor: 'pointer',
              fontWeight: 600, fontSize: 13,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              transition: 'opacity 0.1s',
            }}>
              View Response Plan
              <ChevronRight size={16} />
            </button>

            <button onClick={handleDownloadPDF} disabled={downloading} style={{
              flex: 1, padding: '12px 16px',
              background: 'transparent',
              border: 'var(--border-subtle)',
              borderRadius: 'var(--radius-md)', cursor: downloading ? 'not-allowed' : 'pointer',
              color: 'var(--text-primary)',
              fontWeight: 500, fontSize: 13,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              transition: 'background 0.1s',
            }}>
              <Download size={14} />
              {downloading ? 'Preparing PDF...' : 'Download Report'}
            </button>
          </div>

        </div>
      </div>

      {showPlan && (
        <ResponsePlanPanel
          cellId={cell.cell_id}
          cellName={cell.name}
          riskLevel={riskLevel}
          onClose={() => setShowPlan(false)}
        />
      )}
    </>
  );
}

function MetricCard({ label, value }) {
  return (
    <div style={{
      background: 'var(--bg-glass-hover)',
      border: 'var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: '16px',
    }}>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>{value}</div>
    </div>
  );
}

function ContextRow({ label, value, mono, capitalize }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '12px 16px',
      borderBottom: 'var(--border-subtle)',
    }}>
      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{
        fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
        fontFamily: mono ? 'var(--font-mono)' : 'inherit',
        textTransform: capitalize ? 'capitalize' : 'none',
      }}>
        {value}
      </span>
    </div>
  );
}
