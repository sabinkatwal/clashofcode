import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import { useAuth } from "../context/AuthContext";
import "../styles/auth.css";
import { API_BASE_URL } from "../api/axios";

function Login() {
  const { login, developerLogin, token, loading } = useAuth();
  const [form, setForm] = useState({ username: "", password: "" });
  const [developerUsername, setDeveloperUsername] = useState("");
  const [developerMode, setDeveloperMode] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const googleError = new URLSearchParams(window.location.search).get("error");

  useEffect(() => {
    if (token) navigate("/dashboard", { replace: true });
  }, [token, navigate]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await login(form);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        "Login failed. Check your credentials."
      );
    }
  };

  const handleDeveloperLogin = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await developerLogin(developerUsername);
    } catch {
      setError("Developer access denied.");
    }
  };

  return (
    <section className="page-shell auth-page page-enter">
      <div className="auth-wrap">
        <Card className="auth-intro">
          <h1 className="section-title">Welcome back</h1>
          <p className="section-subtitle">Access your battle rooms and live duels from a calmer, sharper workspace.</p>
        </Card>

        <Card className="auth-card">
          <form onSubmit={handleSubmit}>
            <Input
              label="Username or Email"
              type="text"
              value={form.username}
              onChange={(event) => setForm({ ...form, username: event.target.value })}
              placeholder="your@email.com"
            />
            <Input
              label="Password"
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              placeholder="••••••••"
            />

            {(error || googleError) && <div className="auth-error">{error || googleError}</div>}

            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          <Button
            type="button"
            variant="secondary"
            className="w-full"
            size="lg"
            onClick={() => window.location.assign(`${API_BASE_URL}/auth/google/login`)}
            disabled={loading}
          >
            Continue with Google
          </Button>

          <div className="auth-dev-login">
            <div>
              <p className="auth-dev-login__title">Developer access</p>
              <p className="auth-dev-login__meta">Click below, enter a username, and continue with username-only access.</p>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                setDeveloperMode((current) => !current);
                setError("");
              }}
              disabled={loading}
            >
              {developerMode ? "Hide Developer Login" : "Login as Developer"}
            </Button>
          </div>

          {developerMode && (
            <form className="auth-dev-form" onSubmit={handleDeveloperLogin}>
              <Input
                label="Developer Username"
                type="text"
                value={developerUsername}
                onChange={(event) => setDeveloperUsername(event.target.value)}
                placeholder="Enter a username for developer access"
              />
              <Button type="submit" className="w-full" size="md" disabled={loading || !developerUsername.trim()}>
                Continue as Developer
              </Button>
            </form>
          )}

          <div className="auth-divider"><span>or</span></div>

          <p className="section-subtitle">
            New to Clash of Code?{" "}
            <Link to="/register" className="gradient-text">Create an account</Link>
          </p>
        </Card>
      </div>
    </section>
  );
}

export default Login;
