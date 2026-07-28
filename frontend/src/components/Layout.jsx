import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Globe2, Gavel, LineChart, Settings, HelpCircle, Menu } from 'lucide-react';

export default function Layout() {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <div className="bg-background text-on-background h-screen w-full overflow-hidden flex font-body-md selection:bg-primary selection:text-on-primary relative">
      
      {/* Floating Hamburger Menu & Dropdown */}
      <div className="absolute left-4 top-4 z-50">
        <button 
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="w-10 h-10 flex items-center justify-center rounded-xl bg-surface/80 backdrop-blur-md hover:bg-surface-container-highest border border-outline-variant/50 transition-colors duration-200 shadow-md"
          title="System Menu"
        >
          <Menu className="text-on-surface-variant hover:text-on-surface transition-colors" size={24} />
        </button>

        {/* Dropdown Menu */}
        {dropdownOpen && (
          <>
            {/* Invisible Overlay for click-outside to close */}
            <div 
              className="fixed inset-0 z-40" 
              onClick={() => setDropdownOpen(false)}
            ></div>
            
            <div className="absolute left-0 top-12 w-52 bg-surface-container-highest border border-outline-variant rounded-xl shadow-2xl py-2 z-50 flex flex-col">
              <div className="px-4 py-2 border-b border-outline-variant/50 mb-2">
                <span className="font-headline-sm font-bold text-primary">DisasterMind</span>
              </div>
              
              <NavLink
                to="/"
                onClick={() => setDropdownOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 hover:bg-surface-variant transition-colors w-full ${
                    isActive ? 'text-primary bg-surface-variant/50' : 'text-on-surface-variant hover:text-primary'
                  }`
                }
              >
                <Globe2 size={18} />
                <span>Dashboard</span>
              </NavLink>

              <NavLink
                to="/threats"
                onClick={() => setDropdownOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 hover:bg-surface-variant transition-colors w-full ${
                    isActive ? 'text-primary bg-surface-variant/50' : 'text-on-surface-variant hover:text-primary'
                  }`
                }
              >
                <Gavel size={18} />
                <span>Threats</span>
              </NavLink>

              <NavLink
                to="/analytics"
                onClick={() => setDropdownOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 hover:bg-surface-variant transition-colors w-full mb-2 border-b border-outline-variant/30 pb-4 ${
                    isActive ? 'text-primary bg-surface-variant/50' : 'text-on-surface-variant hover:text-primary'
                  }`
                }
              >
                <LineChart size={18} />
                <span>Analytics</span>
              </NavLink>
              
              <button 
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-3 px-4 py-3 hover:bg-surface-variant text-on-surface-variant hover:text-primary transition-colors text-left w-full mt-2"
              >
                <HelpCircle size={18} />
                <span>Support</span>
              </button>

              <NavLink
                to="/settings"
                onClick={() => setDropdownOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 hover:bg-surface-variant transition-colors w-full ${
                    isActive ? 'text-primary bg-surface-variant/50' : 'text-on-surface-variant hover:text-primary'
                  }`
                }
              >
                <Settings size={18} />
                <span>Settings</span>
              </NavLink>
            </div>
          </>
        )}
      </div>

      {/* Main Content Area (Full Width) */}
      <main className="flex-1 h-screen flex relative overflow-hidden bg-surface-container-lowest w-full">
        <Outlet />
      </main>
    </div>
  );
}
