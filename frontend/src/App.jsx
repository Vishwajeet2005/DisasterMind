import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Layout from './components/Layout';
import GlobalOperations from './pages/GlobalOperations';
import ThreatRoster from './pages/ThreatRoster';
import TelemetryAnalytics from './pages/TelemetryAnalytics';
import SystemConfiguration from './pages/SystemConfiguration';

import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<GlobalOperations />} />
          <Route path="threats" element={<ThreatRoster />} />
          <Route path="analytics" element={<TelemetryAnalytics />} />
          <Route path="settings" element={<SystemConfiguration />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
