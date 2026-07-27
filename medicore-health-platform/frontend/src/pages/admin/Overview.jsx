import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Card, PageHeader } from "../../components/ui";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function AdminOverview() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setMetrics(await api.get(`/reports/daily/${todayISO()}`));
      } catch {
        setMetrics(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const stats = [
    { label: "Active patients", value: metrics?.active_patients ?? "—" },
    { label: "Appointments today", value: metrics?.appointments_total ?? "—" },
    { label: "Completed", value: metrics?.appointments_completed ?? "—" },
    { label: "Cancelled", value: metrics?.appointments_cancelled ?? "—" },
    { label: "Revenue today", value: metrics ? `$${metrics.revenue.toFixed(2)}` : "—" },
  ];

  return (
    <div>
      <PageHeader eyebrow="Hospital overview" title="Admin dashboard" description="Live snapshot of today's activity across the platform." />
      {loading ? (
        <p className="text-sm text-ink/40">Loading…</p>
      ) : !metrics ? (
        <Card><p className="text-sm text-ink/50 py-6 text-center">No metrics ingested for today yet. The nightly rollup job populates this via Reports → Ingest.</p></Card>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {stats.map((s) => (
            <Card key={s.label}>
              <p className="text-xs uppercase tracking-wide text-ink/45 mb-1">{s.label}</p>
              <p className="font-display text-2xl text-ink">{s.value}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
