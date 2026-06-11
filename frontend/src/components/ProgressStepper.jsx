import React, { useState, useEffect } from 'react';
import { Activity, Radio, Cpu, Network, Database, ShieldCheck } from 'lucide-react';

const STEPS = [
  { id: 'uplink', label: 'ESTABLISHING SECURE SATELLITE UPLINK...', icon: Network, duration: 2000 },
  { id: 'telemetry', label: 'EXTRACTING METEOROLOGICAL TELEMETRY...', icon: Radio, duration: 4000 },
  { id: 'firms', label: 'QUERYING NASA FIRMS THERMAL ARRAYS...', icon: Database, duration: 4000 },
  { id: 'ml', label: 'EXECUTING XGBOOST & RANDOM FOREST ENSEMBLE...', icon: Cpu, duration: 6000 },
  { id: 'llm', label: 'SYNTHESIZING THREAT ASSESSMENT...', icon: ShieldCheck, duration: 5000 }
];

const ProgressStepper = () => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    let currentStep = 0;
    
    const advanceStep = () => {
      if (currentStep < STEPS.length - 1) {
        currentStep++;
        setActiveStep(currentStep);
        setTimeout(advanceStep, STEPS[currentStep].duration);
      }
    };

    const timeoutId = setTimeout(advanceStep, STEPS[0].duration);
    return () => clearTimeout(timeoutId);
  }, []);

  return (
    <div className="glass-panel report-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '40px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: 'var(--text-primary)', marginBottom: 40 }}>
        <div style={{ padding: 12, backgroundColor: 'rgba(255, 255, 255, 0.05)', borderRadius: '50%', border: 'var(--border-glass)' }}>
          <Activity size={24} className="spin" style={{ animationDuration: '3s', color: 'var(--text-cyan)' }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span className="mono" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: 2 }}>STATUS</span>
          <span style={{ fontSize: 18, fontWeight: 300, letterSpacing: 1 }}>Executing Threat Analysis</span>
        </div>
      </div>
      
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 20 }}>
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isActive = idx === activeStep;
          const isPast = idx < activeStep;
          
          return (
            <div key={step.id} style={{ 
              display: 'flex', alignItems: 'center', gap: 16,
              opacity: isActive || isPast ? 1 : 0.3,
              transform: isActive ? 'scale(1.02)' : 'scale(1)',
              transition: 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
            }}>
              <div style={{ 
                color: isPast ? 'var(--accent-safe)' : isActive ? 'var(--text-cyan)' : 'var(--text-muted)',
                padding: '8px',
                backgroundColor: isActive ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                borderRadius: '8px',
                border: isActive ? 'var(--border-cyan)' : '1px solid transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Icon size={16} />
              </div>
              <span className="mono" style={{ 
                fontSize: 11, 
                fontWeight: isActive ? 600 : 400,
                color: isPast ? 'var(--text-secondary)' : isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                letterSpacing: 1
              }}>
                {step.label}
              </span>
              {isActive && <div style={{ width: 4, height: 4, borderRadius: '50%', backgroundColor: 'var(--text-cyan)', marginLeft: 'auto', boxShadow: '0 0 8px var(--text-cyan)' }} />}
            </div>
          );
        })}
      </div>
      
      <div className="mono" style={{ marginTop: 40, fontSize: 11, color: '#64748B', textAlign: 'center' }}>
        AWAITING NEURAL NETWORK CLASSIFICATION...
      </div>
    </div>
  );
};

export default ProgressStepper;
