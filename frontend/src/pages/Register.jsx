
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, UserPlus, ShieldCheck } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import Logo from "../components/Logo";

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 8 || password.length > 128) {
      setError("Password must contain 8 to 128 characters.");
      return;
    }

    setSubmitting(true);

    try {
      await register(fullName.trim(), email.trim(), password);

      navigate("/login", {
        replace: true,
        state: { registered: true },
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Registration failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <section className="auth-brand-panel">
        <div className="auth-brand-content">
          <Logo />

          <div className="auth-brand-message">
            <span>WELCOME TO PROOFPOCKET</span>
            <h1>Your important records deserve a smarter home.</h1>
            <p>
              Keep your documents organized, get answers with AI,
              and stay ahead of deadlines.
            </p>
          </div>

          <div className="auth-security">
            <ShieldCheck size={19} />
            One place for your important documents
          </div>
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-mobile-logo">
            <Logo />
          </div>

          <div className="auth-heading">
            <div className="auth-icon">
              <UserPlus size={23} />
            </div>
            <h2>Create your account</h2>
            <p>Start organizing your important documents today.</p>
          </div>

          <form onSubmit={handleSubmit}>
            <label htmlFor="register-name">Full name</label>
            <input
              id="register-name"
              type="text"
              placeholder="Enter your full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              minLength={2}
              maxLength={100}
              autoComplete="name"
              required
            />

            <label htmlFor="register-email">Email address</label>
            <input
              id="register-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />

            <label htmlFor="register-password">Password</label>
            <div className="password-field">
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                placeholder="Minimum 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label="Toggle password visibility"
              >
                {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
              </button>
            </div>

            <label htmlFor="confirm-password">Confirm password</label>
            <input
              id="confirm-password"
              type="password"
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              required
            />

            {error && <div className="form-error">{error}</div>}

            <button
              className="auth-submit"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <div className="auth-switch">
            Already have an account?
            <Link to="/login"> Sign in</Link>
          </div>

          <div className="auth-footer">
            <ShieldCheck size={15} />
            Your personal workspace starts here.
          </div>
        </div>
      </section>
    </div>
  );
}
