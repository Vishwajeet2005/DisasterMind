import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Globe2, Gavel, LineChart, Settings, HelpCircle, Activity } from 'lucide-react';

export default function Layout() {
  return (
    <div className="bg-background text-on-background h-screen w-full overflow-hidden flex font-body-md selection:bg-primary selection:text-on-primary">
      {/* SideNavBar */}
      <nav className="w-sidebar-width h-screen fixed left-0 top-0 border-r border-outline-variant flex flex-col items-center py-4 bg-surface z-50 transition-none justify-between">
        <div className="flex flex-col items-center w-full gap-8">
          {/* Brand Logo */}
          <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-gradient-to-br from-surface-container-highest to-surface-container-low border border-outline-variant/50 shadow-lg cursor-help group" title="System Operator">
            <Activity className="text-primary group-hover:scale-110 transition-transform duration-300" size={20} strokeWidth={2.5} />
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

        {/* Footer Navigation */}
        <div className="flex flex-col w-full px-[2px] gap-2">
          <button aria-label="Support" className="w-full aspect-square flex flex-col items-center justify-center text-on-surface-variant hover:bg-surface-container-highest border border-transparent hover:text-on-surface transition-colors duration-200 group">
            <HelpCircle size={20} strokeWidth={1.5} />
          </button>
          
          <NavLink
            to="/settings"
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
                <Settings size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                {isActive && (
                  <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[3px] rounded-r-full h-1/2 bg-primary"></div>
                )}
              </>
            )}
          </NavLink>
        </div>
      </nav>

      {/* Main Content Area (Offset by sidebar width) */}
      <main className="flex-1 ml-sidebar-width h-screen flex relative overflow-hidden bg-surface-container-lowest">
        <Outlet />
      </main>
    </div>
  );
}
