import { NavLink } from "react-router-dom";
import { LayoutDashboard, BookOpen, Search, Settings } from "lucide-react";
import { cn } from "../../lib/utils";

const NAV = [
  { to: "/",           icon: LayoutDashboard, label: "Dashboard" },
  { to: "/bitacoras",  icon: BookOpen,        label: "Bitácoras" },
  { to: "/work-items", icon: Search,          label: "Work Items" },
  { to: "/settings",   icon: Settings,        label: "Config" },
];

export function Sidebar() {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden sm:flex fixed left-0 top-0 h-full w-60 bg-gray-900 border-r border-gray-800 flex-col z-30">
        <div className="px-5 py-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
              B
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-100">Bitácoras SENA</p>
              <p className="text-xs text-gray-500">Etapa Productiva</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                  isActive
                    ? "bg-blue-600/20 text-blue-400"
                    : "text-gray-400 hover:bg-gray-800 hover:text-gray-100"
                )
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-gray-800">
          <p className="text-xs text-gray-600">Duvan Yair Arciniegas</p>
          <p className="text-xs text-gray-600">ADSO · Linktic SAS</p>
        </div>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-30 bg-gray-900 border-t border-gray-800 flex">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-xs font-medium transition-all touch-manipulation min-h-[56px]",
                isActive
                  ? "text-blue-400"
                  : "text-gray-500 hover:text-gray-300"
              )
            }
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </>
  );
}
