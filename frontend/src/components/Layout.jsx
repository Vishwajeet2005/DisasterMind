import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Globe2, Gavel, LineChart, Settings, HelpCircle, Menu } from 'lucide-react';

export default function Layout() {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <div className="bg-background text-on-background h-screen w-full overflow-hidden flex font-body-md selection:bg-primary selection:text-on-primary">
      {/* SideNavBar */}
      <nav className="w-sidebar-width h-screen fixed left-0 top-0 border-r border-outline-variant flex flex-col items-center py-4 bg-surface z-40 transition-none justify-between">
        <div className="flex flex-col items-center w-full gap-8">
          
          {/* Hamburger Menu & Dropdown */}
          <div className="relative">
            <button 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="w-10 h-10 flex items-center justify-center rounded-xl bg-transparent hover:bg-surface-container-highest border border-transparent hover:border-outline-variant/50 transition-colors duration-200"
              title="System Menu"
            >
              <Menu className="text-on-surface-variant hover:text-on-surface transition-colors" size={24} />
            </button>

            {/* Dropdown Menu */}
            {dropdownOpen && (
              <>
                {/* Invisible Overlay for click-outside to close */}
                <div 
                  className="fixed inset-0 z-50" 
                  onClick={() => setDropdownOpen(false)}
                ></div>
                
                <div className="absolute left-14 top-0 w-48 bg-surface-container-highest border border-outline-variant rounded-xl shadow-2xl py-2 z-50 flex flex-col">
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
          
          {/* Primary Navigation Tabs */}
          <div className="flex flex-col w-full px-[2px] gap-2">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `w-full aspect-square flex flex-col items-center justify-center border group relative transition-colors duration-200 ${
                  isActive
                    ? 'text-primary bg-surface-container-highest border-transparent'
                    : 'text-on-surface-variant hover:bg-surface-container-highest border-transparent hover:text-on-surface'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Globe2 size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                  {isActive && (
                    <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[3px] rounded-r-full h-1/2 bg-primary"></div>
                  )}
                </>
              )}
            </NavLink>

            <NavLink
              to="/threats"
              className={({ isActive }) =>
                `w-full aspect-square flex flex-col items-center justify-center border group relative transition-colors duration-200 ${
                  isActive
                    ? 'text-primary bg-surface-container-highest border-transparent'
                    : 'text-on-surface-variant hover:bg-surface-container-highest border-transparent hover:text-on-surface'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Gavel size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                  {isActive && (
                    <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[3px] rounded-r-full h-1/2 bg-primary"></div>
                  )}
                </>
              )}
            </NavLink>

            <NavLink
              to="/analytics"
              className={({ isActive }) =>
                `w-full aspect-square flex flex-col items-center justify-center border group relative transition-colors duration-200 ${
                  isActive
                    ? 'text-primary bg-surface-container-highest border-transparent'
                    : 'text-on-surface-variant hover:bg-surface-container-highest border-transparent hover:text-on-surface'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <LineChart size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                  {isActive && (
                    <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[3px] rounded-r-full h-1/2 bg-primary"></div>
                  )}
                </>
              )}
            </NavLink>

          </div>
        </div>

        {/* Empty Footer Navigation - Elements moved to dropdown */}
        <div className="flex flex-col w-full px-[2px] gap-2">
        </div>
      </nav>

      {/* Main Content Area (Offset by sidebar width) */}
      <main className="flex-1 ml-sidebar-width h-screen flex relative overflow-hidden bg-surface-container-lowest">
        <Outlet />
      </main>
    </div>
  );
}
