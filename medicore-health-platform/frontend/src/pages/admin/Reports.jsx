import { useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Card, Button, Input, Table, Banner, PageHeader } from "../../components/ui";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function AdminReports() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    metric_date: todayISO(), active_patients: "", appointments_total: "",
    appointments_completed: "", appointments_cancelled: "", revenue: "",
  });

  const load = async () => {
    setLoading(true);
    try {
      setRows(await api.get("/reports/daily"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const ingest = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      const params = new URLSearchParams({
        active_patients: form.active_patients || 0,
        appointments_total: form.appointments_total || 0,
        appointments_completed: form.appointments_completed || 0,
        appointments_cancelled: form.appointments_cancelled || 0,
        revenue: form.revenue || 0,
      });
      await api.post(`/reports/daily/${form.metric_date}/ingest?${params.toString()}`);
      setSuccess(`Metrics saved for ${form.metric_date}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save metrics.");
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    { key: "metric_date", header: "Date" },
    { key: "active_patients", header: "Active patients" },
    { key: "appointments_total", header: "Appointments" },
    { key: "appointments_completed", header: "Completed" },
    { key: "appointments_cancelled", header: "Cancelled" },
    { key: "revenue", header: "Revenue", render: (r) => `$${r.revenue.toFixed(2)}` },
  ];

  return (
    <div>
      <PageHeader eyebrow="Analytics" title="Reports" description="Daily hospital-wide rollups." />

      <div className={user.role === "system_admin" ? "grid grid-cols-1 lg:grid-cols-3 gap-6" : ""}>
        {user.role === "system_admin" && (
          <Card title="Ingest daily metrics" className="lg:col-span-1">
            <form onSubmit={ingest} className="space-y-3">
              {error && <Banner tone="danger">{error}</Banner>}
              {success && <Banner tone="success">{success}</Banner>}
              <Input label="Date" type="date" required value={form.metric_date} onChange={(e) => setForm({ ...form, metric_date: e.target.value })} />
              <Input label="Active patients" type="number" min="0" value={form.active_patients} onChange={(e) => setForm({ ...form, active_patients: e.target.value })} />
              <Input label="Appointments total" type="number" min="0" value={form.appointments_total} onChange={(e) => setForm({ ...form, appointments_total: e.target.value })} />
              <Input label="Completed" type="number" min="0" value={form.appointments_completed} onChange={(e) => setForm({ ...form, appointments_completed: e.target.value })} />
              <Input label="Cancelled" type="number" min="0" value={form.appointments_cancelled} onChange={(e) => setForm({ ...form, appointments_cancelled: e.target.value })} />
              <Input label="Revenue" type="number" step="0.01" min="0" value={form.revenue} onChange={(e) => setForm({ ...form, revenue: e.target.value })} />
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Saving…" : "Save metrics"}
              </Button>
            </form>
          </Card>
        )}

        <Card title="History" className={user.role === "system_admin" ? "lg:col-span-2" : ""}>
          {loading ? <p className="text-sm text-ink/40">Loading…</p> : <Table columns={columns} rows={rows} emptyLabel="No metrics recorded yet." />}
        </Card>
      </div>
    </div>
  );
}
