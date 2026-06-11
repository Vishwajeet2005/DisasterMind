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
    <div className="surface-panel report-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', backgroundColor: '#001529' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--color-critical)', marginBottom: 32 }}>
        <Activity size={24} className="spin" style={{ animationDuration: '2s' }} />
        <span className="mono" style={{ fontSize: 18, fontWeight: 700, letterSpacing: 2 }}>EXECUTING LIVE THREAT ANALYSIS</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === activeStep;
          const isCompleted = index < activeStep;
          
          let color = '#475569'; // Pending (Slate)
          if (isActive) color = '#00BCD4'; // Active (Cyan)
          if (isCompleted) color = '#22C55E'; // Done (Green)

          return (
            <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 16, opacity: isCompleted ? 0.7 : 1 }}>
              <div style={{ 
                width: 32, height: 32, borderRadius: 4, border: `2px solid ${color}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                backgroundColor: isActive ? 'rgba(0, 188, 212, 0.1)' : 'transparent',
                color: color, transition: 'all 0.3s ease'
              }}>
                <Icon size={16} />
              </div>
              <span className="mono" style={{ 
                fontSize: 13, 
                fontWeight: isActive ? 700 : 500,
                color: isActive ? '#FFFFFF' : color,
                transition: 'all 0.3s ease'
              }}>
                {isCompleted ? `[OK] ${step.label.replace('...', ' COMPLETE')}` : step.label}
              </span>
              {isActive && <div className="dot" style={{ backgroundColor: '#00BCD4', boxShadow: '0 0 8px #00BCD4', marginLeft: 'auto' }}></div>}
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
