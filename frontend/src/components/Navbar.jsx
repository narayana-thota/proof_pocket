
import { Search, Bell, ChevronDown, Menu } from "lucide-react";

export default function Navbar({ onMenuClick }) {
  return (
    <header className="pp-navbar">
      <div className="pp-navbar-left">
        <button
          className="pp-menu-button"
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation menu"
        >
          <Menu size={21} />
        </button>

        <div className="pp-global-search">
          <Search size={18} />

          <input
            type="search"
            placeholder="Search documents, chats, reminders..."
            aria-label="Search ProofPocket"
          />

          <span className="pp-search-shortcut">Ctrl K</span>
        </div>
      </div>

      <div className="pp-navbar-right">
        <button
          className="pp-notification-button"
          type="button"
          aria-label="Notifications"
          title="Notifications"
        >
          <Bell size={20} />
          <span className="pp-notification-dot" />
        </button>

        <div className="pp-navbar-divider" />

        <button
          className="pp-profile-button"
          type="button"
          onClick={() => {
            window.location.href = "/account";
          }}
        >
          <div className="pp-profile-avatar">N</div>

          <div className="pp-profile-details">
            <strong>My Account</strong>
            <span>Personal workspace</span>
          </div>

          <ChevronDown size={16} />
        </button>
      </div>
    </header>
  );
}
