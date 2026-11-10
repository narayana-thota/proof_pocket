import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Settings as SettingsIcon,
  Palette,
  Bell,
  ShieldCheck,
  UserRound,
  Info,
  Moon,
  Sun,
  Check,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import "./Settings.css";

const STORAGE_KEY = "proofpocket_preferences";

const defaultPreferences = {
  theme: "light",
  reminderAlerts: true,
  emailAlerts: false,
  productUpdates: false,
};

function readPreferences() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved
      ? { ...defaultPreferences, ...JSON.parse(saved) }
      : defaultPreferences;
  } catch {
    return defaultPreferences;
  }
}

function PreferenceToggle({ checked, onChange, label }) {
  return (
    <button
      type="button"
      className={`settings-toggle ${checked ? "is-on" : ""}`}
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
    >
      <span />
    </button>
  );
}

function SettingsRow({ title, description, checked, onChange, label }) {
  return (
    <div className="settings-row">
      <div className="settings-row-copy">
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
      <PreferenceToggle
        checked={checked}
        onChange={onChange}
        label={label || title}
      />
    </div>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState(readPreferences);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
      document.documentElement.dataset.theme = preferences.theme;
      setSaved(true);
      const timeout = window.setTimeout(() => setSaved(false), 1600);
      return () => window.clearTimeout(timeout);
    } catch {
      setSaved(false);
    }
  }, [preferences]);

  const updatePreference = (key, value) => {
    setPreferences((current) => ({ ...current, [key]: value }));
  };

  const resetPreferences = () => {
    setPreferences(defaultPreferences);
  };

  return (
    <main className="settings-page">
      <header className="settings-heading">
        <div>
          <span className="settings-eyebrow">PREFERENCES</span>
          <h1>Settings</h1>
          <p>Manage your ProofPocket experience and personal preferences.</p>
        </div>
        <div className="settings-heading-icon">
          <SettingsIcon size={23} />
        </div>
      </header>

      <div className="settings-save-status" aria-live="polite">
        {saved && (
          <span>
            <Check size={14} /> Preferences saved on this device
          </span>
        )}
      </div>

      <section className="settings-card">
        <div className="settings-card-heading">
          <div className="settings-card-icon purple">
            <Palette size={19} />
          </div>
          <div>
            <h2>Appearance</h2>
            <p>Choose how ProofPocket looks on this device.</p>
          </div>
        </div>

        <div className="settings-theme-options">
          <button
            type="button"
            className={`settings-theme-option ${preferences.theme === "light" ? "selected" : ""}`}
            onClick={() => updatePreference("theme", "light")}
            aria-pressed={preferences.theme === "light"}
          >
            <span className="settings-theme-preview light-preview">
              <Sun size={20} />
              <i />
              <i />
              <i />
            </span>
            <span className="settings-theme-label">Light</span>
            {preferences.theme === "light" && <Check size={16} />}
          </button>

          <button
            type="button"
            className={`settings-theme-option ${preferences.theme === "dark" ? "selected" : ""}`}
            onClick={() => updatePreference("theme", "dark")}
            aria-pressed={preferences.theme === "dark"}
          >
            <span className="settings-theme-preview dark-preview">
              <Moon size={20} />
              <i />
              <i />
              <i />
            </span>
            <span className="settings-theme-label">Dark</span>
            {preferences.theme === "dark" && <Check size={16} />}
          </button>
        </div>
        <p className="settings-inline-note">
          Theme preference is stored locally. Dark styling is currently applied
          to the Settings page and application shell; some existing pages may
          retain light surfaces.
        </p>
      </section>

      <section className="settings-card">
        <div className="settings-card-heading">
          <div className="settings-card-icon blue">
            <Bell size={19} />
          </div>
          <div>
            <h2>Notification preferences</h2>
            <p>Choose which types of updates you want to keep enabled.</p>
          </div>
        </div>

        <div className="settings-rows">
          <SettingsRow
            title="Reminder alerts"
            description="Keep reminder alerts enabled in your preferences."
            checked={preferences.reminderAlerts}
            onChange={(value) => updatePreference("reminderAlerts", value)}
          />
          <SettingsRow
            title="Email notifications"
            description="Preference for receiving reminder updates by email."
            checked={preferences.emailAlerts}
            onChange={(value) => updatePreference("emailAlerts", value)}
          />
          <SettingsRow
            title="Product updates"
            description="Preference for occasional ProofPocket feature announcements."
            checked={preferences.productUpdates}
            onChange={(value) => updatePreference("productUpdates", value)}
          />
        </div>

        <div className="settings-notice">
          <Info size={16} />
          <p>
            These are saved preferences only. Email, browser, and push
            notifications are not connected to a delivery service yet.
          </p>
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-card-heading">
          <div className="settings-card-icon green">
            <ShieldCheck size={19} />
          </div>
          <div>
            <h2>Security</h2>
            <p>Information about your current account session.</p>
          </div>
        </div>

        <div className="settings-security-row">
          <div>
            <strong>Signed-in account</strong>
            <p>{user?.email || "Account information unavailable"}</p>
          </div>
          <span className="settings-session-badge">
            <span /> Authenticated
          </span>
        </div>
        <div className="settings-security-row">
          <div>
            <strong>Password</strong>
            <p>Your password is securely hashed and is not displayed.</p>
          </div>
          <span className="settings-unavailable">Not editable here</span>
        </div>
      </section>

      <section className="settings-card settings-account-card">
        <div className="settings-card-heading">
          <div className="settings-card-icon violet">
            <UserRound size={19} />
          </div>
          <div>
            <h2>Account</h2>
            <p>View your registered profile information.</p>
          </div>
        </div>
        <Link to="/account" className="settings-navigation-link">
          <span>Open account details</span>
          <ChevronRight size={18} />
        </Link>
      </section>

      <section className="settings-footer-card">
        <div className="settings-footer-icon">
          <Info size={18} />
        </div>
        <div>
          <strong>ProofPocket</strong>
          <p>Personal document and reminder management.</p>
          <span>Preferences are stored in this browser, not in your account database.</span>
        </div>
        <button
          type="button"
          className="settings-reset-button"
          onClick={resetPreferences}
        >
          <RotateCcw size={14} />
          Reset
        </button>
      </section>
    </main>
  );
}
