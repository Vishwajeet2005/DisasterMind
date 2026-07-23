import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Globe2, Gavel, LineChart, Settings, HelpCircle } from 'lucide-react';

export default function Layout() {
  return (
    <div className="bg-background text-on-background h-screen w-full overflow-hidden flex font-body-md selection:bg-primary selection:text-on-primary">
      {/* SideNavBar */}
      <nav className="w-sidebar-width h-screen fixed left-0 top-0 border-r border-outline-variant flex flex-col items-center py-4 bg-surface z-50 transition-none justify-between">
        <div className="flex flex-col items-center w-full gap-8">
          {/* Brand Logo */}
          <div className="w-10 h-10 border border-outline-variant flex items-center justify-center bg-surface-container-highest cursor-help group" title="System Operator">
            <span className="font-headline-md font-bold text-primary">SC</span>
          </div>
          
          {/* Primary Navigation Tabs */}
          <div className="flex flex-col w-full px-[2px] gap-2">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `w-full aspect-square flex flex-col items-center justify-center border group relative transition-none ${
                  isActive
                    ? 'bg-primary text-on-primary border-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-highest border-transparent hover:border-outline-variant'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Globe2 size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                  {isActive && (
                    <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[2px] h-1/2 bg-primary"></div>
                  )}
                </>
              )}
            </NavLink>

            <NavLink
              to="/threats"
              className={({ isActive }) =>
                `w-full aspect-square flex flex-col items-center justify-center border group relative transition-none ${
                  isActive
                    ? 'bg-primary text-on-primary border-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-highest border-transparent hover:border-outline-variant'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Gavel size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                  {isActive && (
                    <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[2px] h-1/2 bg-primary"></div>
                  )}
                </>
              )}
            </NavLink>

            <NavLink
              to="/analytics"
              className={({ isActive }) =>
                `w-full aspect-square flex flex-col items-center justify-center border group relative transition-none ${
                  isActive
                    ? 'bg-primary text-on-primary border-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-highest border-transparent hover:border-outline-variant'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <LineChart size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                  {isActive && (
                    <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[2px] h-1/2 bg-primary"></div>
                  )}
                </>
              )}
            </NavLink>

          </div>
        </div>

        {/* Footer Navigation */}
        <div className="flex flex-col w-full px-[2px] gap-2">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `w-full aspect-square flex flex-col items-center justify-center border group relative transition-none ${
                isActive
                  ? 'bg-primary text-on-primary border-primary'
                  : 'text-on-surface-variant hover:bg-surface-container-highest border-transparent hover:border-outline-variant'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Settings size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                {isActive && (
                  <div className="absolute left-[-3px] top-1/2 -translate-y-1/2 w-[2px] h-1/2 bg-primary"></div>
                )}
              </>
            )}
          </NavLink>
          
          <button aria-label="Support" className="w-full aspect-square flex flex-col items-center justify-center text-on-surface-variant hover:bg-surface-container-highest border border-transparent hover:border-outline-variant transition-none group">
            <HelpCircle size={20} strokeWidth={1.5} />
          </button>
          <div className="mt-4 font-data-tabular text-[9px] text-on-surface-variant rotate-180 [writing-mode:vertical-lr] text-center w-full">V 4.2.0</div>
        </div>
      </nav>

      {/* Main Content Area (Offset by sidebar width) */}
      <main className="flex-1 ml-sidebar-width h-screen flex relative overflow-hidden bg-surface-container-lowest">
        <Outlet />
      </main>
    </div>
  );
}
