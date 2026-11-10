
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, ShieldCheck, LockKeyhole } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import Logo from "../components/Logo";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to log in. Please check your credentials."
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
            <span>YOUR DOCUMENTS. ALWAYS AT HAND.</span>
            <h1>Everything important, in one secure pocket.</h1>
            <p>
              Organize your documents, ask questions with AI,
              and never miss an important deadline.
            </p>
          </div>
          <div className="auth-security">
            <ShieldCheck size={19} />
            Your personal document workspace
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
              <LockKeyhole size={23} />
            </div>
            <h2>Welcome back</h2>
            <p>Sign in to continue to your ProofPocket workspace.</p>
          </div>

          <form onSubmit={handleSubmit}>
            <label htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />

            <label htmlFor="login-password">Password</label>
            <div className="password-field">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                minLength={8}
                maxLength={128}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
              </button>
            </div>

            {error && <div className="form-error">{error}</div>}

            <button
              className="auth-submit"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <div className="auth-switch">
            Don't have an account?
            <Link to="/register"> Create account</Link>
          </div>

          <div className="auth-footer">
            <ShieldCheck size={15} />
            Your documents are protected with ProofPocket.
          </div>
        </div>
      </section>
    </div>
  );
}
