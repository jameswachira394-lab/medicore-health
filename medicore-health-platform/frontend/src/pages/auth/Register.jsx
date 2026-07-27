import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Button, Input, Banner } from "../../components/ui";

export default function Register() {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register({ ...form, role: "patient" });
      await login(form.email, form.password);
      navigate("/patient/onboarding", { replace: true });
    } catch (err) {
      setError(err.detail || "Could not create your account.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <p className="font-display text-2xl text-brand-dim tracking-tight">MediCore</p>
          <p className="text-sm text-ink/50 mt-1">Create your patient account</p>
        </div>

        <form onSubmit={onSubmit} className="bg-surface border border-line rounded-xl p-6 space-y-4">
          {error && <Banner tone="danger">{error}</Banner>}
          <Input
            label="Full name"
            required
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
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
            minLength={8}
            required
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </Button>
        </form>

        <p className="text-center text-sm text-ink/50 mt-5">
          Already registered?{" "}
          <Link to="/login" className="text-brand-dim font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
