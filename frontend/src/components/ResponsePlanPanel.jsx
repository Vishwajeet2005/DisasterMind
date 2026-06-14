import React, { useState, useEffect } from 'react';
import { X, AlertTriangle, Shield, Clock, Phone, MapPin, ChevronRight, Activity, Crosshair, Navigation, Building2, ShieldAlert } from 'lucide-react';
import API_CONFIG from '../api';

const API_BASE = API_CONFIG;

const RISK_THEME = {
  CRITICAL: { color: 'var(--risk-critical-color)', bg: 'var(--risk-critical-bg)', border: 'var(--risk-critical-border)' },
  HIGH:     { color: 'var(--risk-high-color)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)' },
  MODERATE: { color: 'var(--risk-moderate-color)', bg: 'var(--risk-moderate-bg)', border: 'var(--risk-moderate-border)' },
  LOW:      { color: 'var(--risk-low-color)',      bg: 'var(--risk-low-bg)',      border: 'var(--risk-low-border)' },
};

export default function ResponsePlanPanel({ cellId, cellName, riskLevel, onClose }) {
  const [plan,      setPlan]      = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => { handleGenerate(); }, [cellId]);

  const rc = RISK_THEME[riskLevel] || RISK_THEME.LOW;

  const handleGenerate = async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/plan/${cellId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPlan(data.plan);
    } catch {
      setError('Failed to generate response plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const TABS = [
    { id: 'overview',  label: 'Situation',  icon: AlertTriangle },
    { id: 'resources', label: 'Resources',  icon: Shield        },
    { id: 'timeline',  label: 'Timeline',   icon: Clock         },
    { id: 'comms',     label: 'Comms',      icon: Phone         },
  ];

  const p = plan;

  return (
    <div
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'transparent',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24,
      }}
    >
      <div style={{
        width: '100%', maxWidth: 840,
        height: '90vh',
        background: 'var(--bg-glass-heavy)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        borderRadius: 'var(--radius-lg)',
        border: 'var(--border-glass)',
        boxShadow: 'var(--shadow-glass), 0 24px 80px rgba(0,0,0,0.5)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}>

        {/* ── Header ─────────────────────────────────────────────── */}
        <div style={{
          padding: '24px 32px',
          borderBottom: 'var(--border-subtle)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  padding: '6px 12px', background: rc.bg, border: `1px solid ${rc.border}`,
                  borderRadius: 'var(--radius-sm)',
                }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: rc.color }} />
                  <span style={{ fontSize: 13, fontWeight: 600, color: rc.color }}>{riskLevel} RISK</span>
                </div>
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Response Plan</span>
              </div>
              
              <div style={{ fontSize: 24, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                {cellName}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <button onClick={handleGenerate} disabled={loading} style={{
                padding: '8px 16px', background: 'transparent',
                border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)', cursor: loading ? 'not-allowed' : 'pointer',
                fontWeight: 500, fontSize: 13,
              }}>
                Regenerate
              </button>
              <button onClick={onClose} style={{
                background: 'transparent', border: 'none', color: 'var(--text-secondary)',
                cursor: 'pointer', padding: 4,
              }}>
                <X size={24} />
              </button>
            </div>
          </div>

          {/* Tab Navigation */}
          {p && !loading && !error && (
            <div style={{ display: 'flex', gap: 24 }}>
              {TABS.map(tab => {
                const IconComp = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                    padding: '8px 0', border: 'none', background: 'transparent',
                    borderBottom: isActive ? `2px solid var(--text-primary)` : '2px solid transparent',
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    fontWeight: 600, fontSize: 14, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: 8, transition: 'all 0.1s',
                  }}>
                    <IconComp size={16} />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Body ────────────────────────────────────────────────── */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>

          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
              <div style={{
                width: 40, height: 40, borderRadius: '50%',
                border: `2px solid rgba(255,255,255,0.1)`,
                borderTop: `2px solid ${rc.color}`,
                margin: '0 auto 20px',
                animation: 'spin 0.8s linear infinite',
              }} />
              <div>Generating intelligent response plan...</div>
            </div>
          )}

          {error && (
            <div style={{
              background: 'var(--risk-critical-bg)', border: 'var(--risk-critical-border)',
              padding: 24, borderRadius: 'var(--radius-md)', color: 'var(--text-primary)',
            }}>
              <AlertTriangle size={24} color="var(--risk-critical-color)" style={{ marginBottom: 12 }} />
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Error</div>
              <div>{error}</div>
            </div>
          )}

          {!loading && !error && p && (
            <>
              {activeTab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
                  <section>
                    <SectionTitle title="Situation Overview" />
                    <div style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--text-primary)' }}>
                      {p.situation_overview}
                    </div>
                  </section>

                  {p.do_not?.length > 0 && (
                    <section>
                      <SectionTitle title="Critical Directives" />
                      <div style={{ display: 'grid', gap: 12 }}>
                        {p.do_not.map((rule, i) => (
                          <div key={i} style={{
                            display: 'flex', alignItems: 'center', gap: 12,
                            padding: '12px 16px', background: 'var(--risk-critical-bg)',
                            border: 'var(--risk-critical-border)', borderRadius: 'var(--radius-md)',
                            color: 'var(--text-primary)',
                          }}>
                            <ShieldAlert size={16} color="var(--risk-critical-color)" flexShrink={0} />
                            <span style={{ fontSize: 14 }}>{rule}</span>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}

                  {p.evacuation_zones?.length > 0 && (
                    <section>
                      <SectionTitle title="Evacuation Zones" />
                      <div style={{ display: 'grid', gap: 12 }}>
                        {p.evacuation_zones.map((z, i) => (
                          <div key={i} style={{
                            display: 'flex', alignItems: 'flex-start', gap: 16,
                            padding: '16px 20px', background: 'var(--bg-glass-hover)',
                            border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                          }}>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                                Zone {z.zone}: {z.area}
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 8 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
                                  <MapPin size={14} /> Est. Pop: {z.population}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
                                  <Navigation size={14} /> Route: {z.route}
                                </div>
                              </div>
                            </div>
                            <div style={{
                              padding: '4px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600,
                              background: z.priority === 'IMMEDIATE' ? 'var(--risk-critical-bg)' : z.priority === 'URGENT' ? 'var(--risk-high-bg)' : 'var(--risk-low-bg)',
                              color: z.priority === 'IMMEDIATE' ? 'var(--risk-critical-color)' : z.priority === 'URGENT' ? 'var(--risk-high-color)' : 'var(--risk-low-color)',
                            }}>
                              {z.priority}
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                </div>
              )}

              {activeTab === 'resources' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
                  {p.ndrf_deployment && (
                    <section>
                      <SectionTitle title="NDRF Deployment Strategy" />
                      <div style={{
                        padding: 24, background: 'var(--bg-glass-hover)',
                        border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                          <Crosshair size={24} color={rc.color} />
                          <div>
                            <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>
                              {p.ndrf_deployment.battalion}
                            </div>
                            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                              Base: {p.ndrf_deployment.base_location} &nbsp;·&nbsp; ETA: {p.ndrf_deployment.eta_hours} hrs
                            </div>
                          </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: 16, borderTop: 'var(--border-subtle)', paddingTop: 16 }}>
                          <div>
                            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Teams Req.</div>
                            <div style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)' }}>{p.ndrf_deployment.teams_required}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Initial Objective</div>
                            <div style={{ fontSize: 15, color: 'var(--text-primary)' }}>{p.ndrf_deployment.advance_team_action}</div>
                          </div>
                        </div>
                      </div>
                    </section>
                  )}

                  <section>
                    <SectionTitle title="Physical Resources" />
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                      {Object.entries(p.resources || {}).map(([key, val]) => (
                        <div key={key} style={{
                          padding: 20, background: 'var(--bg-glass-hover)',
                          border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                          display: 'flex', flexDirection: 'column', gap: 8,
                        }}>
                          <div style={{ fontSize: 24, fontWeight: 600, color: 'var(--text-primary)' }}>{val}</div>
                          <div style={{ fontSize: 13, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                            {key.replace(/_/g, ' ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section>
                    <SectionTitle title="Supply Requirements" />
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                      {Object.entries(p.supply_requirements || {}).map(([key, val]) => (
                        <div key={key} style={{
                          padding: 20, background: 'var(--bg-glass-hover)',
                          border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                          display: 'flex', flexDirection: 'column', gap: 8,
                        }}>
                          <div style={{ fontSize: 24, fontWeight: 600, color: 'var(--text-primary)' }}>{val}</div>
                          <div style={{ fontSize: 13, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                            {key.replace(/_/g, ' ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              )}

              {activeTab === 'timeline' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
                  <section>
                    <SectionTitle title="Action Timeline" />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {p.action_timeline?.map((step, i) => (
                        <div key={i} style={{
                          display: 'flex', gap: 24, padding: 20,
                          background: 'var(--bg-glass-hover)', border: 'var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                        }}>
                          <div style={{
                            width: 100, flexShrink: 0, fontSize: 14, fontWeight: 600,
                            color: 'var(--text-primary)', borderRight: 'var(--border-subtle)',
                          }}>
                            {step.window || step.hour}
                          </div>
                          <div style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            {step.action}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              )}

              {activeTab === 'comms' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
                  <section>
                    <SectionTitle title="Coordination Agencies" />
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                      {p.coordination_agencies?.map(ag => (
                        <div key={ag} style={{
                          padding: '8px 16px', background: 'var(--bg-glass-hover)',
                          border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                          fontSize: 14, color: 'var(--text-primary)', fontWeight: 500,
                        }}>
                          {ag}
                        </div>
                      ))}
                    </div>
                  </section>

                  <section>
                    <SectionTitle title="Communication Strategy" />
                    <div style={{
                      padding: 24, background: 'var(--bg-glass-hover)',
                      border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                      fontSize: 15, color: 'var(--text-primary)', lineHeight: 1.6,
                    }}>
                      {p.communication_plan}
                    </div>
                  </section>

                  <section>
                    <SectionTitle title="Standby Medical Facilities" />
                    <div style={{ display: 'grid', gap: 12 }}>
                      {p.hospitals_on_standby?.map(h => (
                        <div key={h} style={{
                          display: 'flex', alignItems: 'center', gap: 12,
                          padding: '16px 20px', background: 'var(--bg-glass-hover)',
                          border: 'var(--border-subtle)', borderRadius: 'var(--radius-md)',
                        }}>
                          <Building2 size={18} color="var(--text-secondary)" />
                          <span style={{ fontSize: 15, color: 'var(--text-primary)' }}>{h}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ title }) {
  return (
    <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 20 }}>
      {title}
    </div>
  );
}
