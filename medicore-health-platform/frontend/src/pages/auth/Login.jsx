import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Button, Input, Banner } from "../../components/ui";

const HOME_BY_ROLE = {
  patient: "/patient",
  doctor: "/doctor",
  nurse: "/doctor",
  receptionist: "/admin",
  hospital_admin: "/admin",
  system_admin: "/admin",
};

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "", mfa_code: "" });
  const [needsMfa, setNeedsMfa] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const me = await login(form.email, form.password, form.mfa_code || undefined);
      const dest = location.state?.from?.pathname || HOME_BY_ROLE[me.role] || "/";
      navigate(dest, { replace: true });
    } catch (err) {
      if (err.detail === "Invalid or missing MFA code") {
        setNeedsMfa(true);
      } else {
        setError(err.detail || "Something went wrong. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <p className="font-display text-2xl text-brand-dim tracking-tight">MediCore</p>
          <p className="text-sm text-ink/50 mt-1">Sign in to your account</p>
        </div>

        <form onSubmit={onSubmit} className="bg-surface border border-line rounded-xl p-6 space-y-4">
          {error && <Banner tone="danger">{error}</Banner>}
          <Input
            label="Email"
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <Input
            label="Password"
            type="password"
            required
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          {needsMfa && (
            <Input
              label="Authentication code"
              placeholder="6-digit code"
              value={form.mfa_code}
              onChange={(e) => setForm({ ...form, mfa_code: e.target.value })}
            />
          )}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <p className="text-center text-sm text-ink/50 mt-5">
          New patient?{" "}
          <Link to="/register" className="text-brand-dim font-medium hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
