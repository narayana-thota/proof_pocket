import { useMemo } from "react";
import { useAuth } from "../context/AuthContext";
import {
  UserRound,
  Mail,
  Fingerprint,
  ShieldCheck,
  LockKeyhole,
  Info,
} from "lucide-react";
import "./Account.css";

function getInitials(name = "") {
  return name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("") || "U";
}

function DetailItem({ icon: Icon, label, value }) {
  return (
    <div className="account-detail">
      <div className="account-detail-icon">
        <Icon size={18} strokeWidth={1.8} />
      </div>

      <div className="account-detail-copy">
        <span className="account-detail-label">{label}</span>
        <span className="account-detail-value">{value || "Not available"}</span>
      </div>
    </div>
  );
}

export default function Account() {
  const { user, loading } = useAuth();

  const displayName = user?.full_name || "ProofPocket User";
  const initials = useMemo(() => getInitials(displayName), [displayName]);

  if (loading) {
    return (
      <main className="account-page">
        <div className="account-loading">
          <span className="account-spinner" />
          <p>Loading your account...</p>
        </div>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="account-page">
        <section className="account-empty-state">
          <div className="account-empty-icon">
            <UserRound size={24} />
          </div>
          <h2>Account information unavailable</h2>
          <p>We couldn't load your profile. Please sign in again and revisit this page.</p>
        </section>
      </main>
    );
  }

  return (
    <main className="account-page">
      <header className="account-page-header">
        <div>
          <span className="account-eyebrow">PERSONAL SPACE</span>
          <h1>My Account</h1>
          <p>View the personal information associated with your ProofPocket account.</p>
        </div>
        <div className="account-header-icon">
          <UserRound size={23} strokeWidth={1.7} />
        </div>
      </header>

      <section className="account-profile-card">
        <div className="account-profile-main">
          <div className="account-avatar" aria-label={`${displayName} initials`}>
            {initials}
          </div>

          <div className="account-profile-text">
            <span className="account-profile-label">YOUR PROFILE</span>
            <h2>{displayName}</h2>
            <p>{user.email || "Email address unavailable"}</p>
          </div>
        </div>

        <div className="account-readonly-pill">
          <ShieldCheck size={15} />
          <span>Verified session</span>
        </div>
      </section>

      <section className="account-section">
        <div className="account-section-heading">
          <div>
            <h2>Personal information</h2>
            <p>These details come from your registered account.</p>
          </div>
          <span className="account-readonly-label">READ ONLY</span>
        </div>

        <div className="account-details-card">
          <DetailItem
            icon={UserRound}
            label="Full name"
            value={user.full_name}
          />
          <div className="account-detail-divider" />
          <DetailItem
            icon={Mail}
            label="Email address"
            value={user.email}
          />
          <div className="account-detail-divider" />
          <DetailItem
            icon={Fingerprint}
            label="User ID"
            value={user.user_id != null ? `#${user.user_id}` : null}
          />
        </div>
      </section>

      <section className="account-security-card">
        <div className="account-security-icon">
          <LockKeyhole size={20} />
        </div>
        <div className="account-security-copy">
          <h3>Your account security</h3>
          <p>
            Your password is securely hashed by the backend and is never
            displayed on this page. Profile editing and password changes are
            not available in the current version.
          </p>
        </div>
        <Info className="account-security-info" size={18} />
      </section>
    </main>
  );
}
