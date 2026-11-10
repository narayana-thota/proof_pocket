
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  CalendarDays,
  UserRound,
  Settings,
  LogOut,
  X,
  ShieldCheck,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import Logo from "./Logo";

const mainLinks = [
  { name: "Overview", path: "/", icon: LayoutDashboard, end: true },
  { name: "My Documents", path: "/documents", icon: FileText },
  { name: "AI Document Chat", path: "/chat", icon: MessageSquare },
  { name: "Reminders", path: "/reminders", icon: CalendarDays },
];

export default function Sidebar({ mobileOpen = false, onClose }) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login", { replace: true });
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <>
      {mobileOpen && (
        <button
          className="pp-sidebar-backdrop"
          aria-label="Close navigation"
          onClick={onClose}
        />
      )}

      <aside className={`pp-sidebar ${mobileOpen ? "pp-sidebar-open" : ""}`}>
        <div className="pp-sidebar-header">
          <Logo />

          <button
            className="pp-sidebar-close"
            type="button"
            onClick={onClose}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <div className="pp-workspace">
          <div className="pp-workspace-icon">
            <ShieldCheck size={19} />
          </div>
          <div>
            <strong>Personal Workspace</strong>
            <span>Your secure library</span>
          </div>
        </div>

        <div className="pp-nav-label">WORKSPACE</div>

        <nav className="pp-sidebar-menu">
          {mainLinks.map(({ name, path, icon: Icon, end }) => (
            <NavLink
              key={path}
              to={path}
              end={Boolean(end)}
              onClick={onClose}
              title={name}
              className={({ isActive }) =>
                `pp-sidebar-link ${isActive ? "active" : ""}`
              }
            >
              <Icon size={19} strokeWidth={1.9} />
              <span>{name}</span>
            </NavLink>
          ))}
        </nav>

        <div className="pp-sidebar-bottom">
          <div className="pp-nav-label">PREFERENCES</div>

          <NavLink
            to="/account"
            onClick={onClose}
            className={({ isActive }) =>
              `pp-sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <UserRound size={19} />
            <span>Account</span>
          </NavLink>

          <NavLink
            to="/settings"
            onClick={onClose}
            className={({ isActive }) =>
              `pp-sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <Settings size={19} />
            <span>Settings</span>
          </NavLink>

          <button
            className="pp-sidebar-link pp-logout"
            type="button"
            onClick={handleLogout}
          >
            <LogOut size={19} />
            <span>Sign out</span>
          </button>
        </div>

        <div className="pp-sidebar-footer">
          <div className="pp-footer-shield">
            <ShieldCheck size={17} />
          </div>
          <div>
            <strong>Your data stays protected</strong>
            <span>Secure document storage</span>
          </div>
        </div>
      </aside>
    </>
  );
}
