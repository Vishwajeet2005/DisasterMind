import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Globe2, Gavel, LineChart, Settings, HelpCircle, Menu } from 'lucide-react';

export default function Layout() {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <div className="bg-background text-on-background h-screen w-full overflow-hidden flex font-body-md selection:bg-primary selection:text-on-primary relative">
      
      {/* Floating Hamburger Menu & Dropdown */}
      <div className="absolute left-[24px] top-[24px] z-50">
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
            
            <div className="absolute left-0 top-12 w-56 bg-surface/80 backdrop-blur-xl border border-outline-variant/50 rounded-2xl shadow-[0_16px_40px_rgba(0,0,0,0.6)] py-3 z-50 flex flex-col overflow-hidden">
              <div className="px-5 py-2 border-b border-outline-variant/30 mb-2">
                <span className="font-headline-sm font-bold text-primary">DisasterMind</span>
              </div>
              
              <NavLink
                to="/"
                onClick={() => setDropdownOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-5 py-3 mx-2 rounded-xl transition-all duration-200 ${
                    isActive ? 'text-primary bg-primary/10 font-bold shadow-[inset_4px_0_0_0_rgba(168,199,250,1)]' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/50'
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
                  `flex items-center gap-3 px-5 py-3 mx-2 rounded-xl transition-all duration-200 ${
                    isActive ? 'text-primary bg-primary/10 font-bold shadow-[inset_4px_0_0_0_rgba(168,199,250,1)]' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/50'
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
                  `flex items-center gap-3 px-5 py-3 mx-2 rounded-xl transition-all duration-200 mb-2 ${
                    isActive ? 'text-primary bg-primary/10 font-bold shadow-[inset_4px_0_0_0_rgba(168,199,250,1)]' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/50'
                  }`
                }
              >
                <LineChart size={18} />
                <span>Analytics</span>
              </NavLink>
              
              <div className="mx-4 border-t border-outline-variant/30 my-1"></div>
              
              <button 
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-3 px-5 py-3 mx-2 mt-1 rounded-xl transition-all duration-200 text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/50 text-left"
              >
                <HelpCircle size={18} />
                <span>Support</span>
              </button>

              <NavLink
                to="/settings"
                onClick={() => setDropdownOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-5 py-3 mx-2 rounded-xl transition-all duration-200 ${
                    isActive ? 'text-primary bg-primary/10 font-bold shadow-[inset_4px_0_0_0_rgba(168,199,250,1)]' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/50'
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
