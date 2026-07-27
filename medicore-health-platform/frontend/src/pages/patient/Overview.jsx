import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Card, StatusBadge, PageHeader } from "../../components/ui";
export default function PatientOverview() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [appts, inv] = await Promise.all([
          api.get("/appointments"),
          api.get(`/billing/patients/${user.id}/invoices`),
        ]);
        setAppointments(appts);
        setInvoices(inv);
      } finally {
        setLoading(false);
      }
    })();
  }, [user.id]);

  const upcoming = appointments
    .filter((a) => ["requested", "confirmed"].includes(a.status))
    .sort((a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start))
    .slice(0, 3);

  const outstanding = invoices.filter((i) => i.status !== "paid" && i.status !== "cancelled");

  return (
    <div>
      <PageHeader
        eyebrow="Welcome back"
        title={`Hi, ${user.full_name?.split(" ")[0] || "there"}`}
        description="Here's what's coming up in your care."
        action={
          <Link
            to="/patient/find-a-doctor"
            className="inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium bg-brand text-white hover:bg-brand-dim transition-colors"
          >
            Book an appointment
          </Link>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card title="Upcoming appointments" action={<Link to="/patient/appointments" className="text-sm text-brand-dim font-medium hover:underline">View all</Link>}>
          {loading ? (
            <p className="text-sm text-ink/40">Loading…</p>
          ) : upcoming.length === 0 ? (
            <p className="text-sm text-ink/50 py-4">Nothing scheduled. <Link to="/patient/find-a-doctor" className="text-brand-dim hover:underline">Find a doctor</Link> to book one.</p>
          ) : (
            <ul className="space-y-3">
              {upcoming.map((a) => (
                <li key={a.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-ink">{new Date(a.scheduled_start).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}</p>
                    <p className="text-xs text-ink/50">{a.reason || "General consultation"}</p>
                  </div>
                  <StatusBadge status={a.status} />
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Billing" action={<Link to="/patient/billing" className="text-sm text-brand-dim font-medium hover:underline">View all</Link>}>
          {loading ? (
            <p className="text-sm text-ink/40">Loading…</p>
          ) : outstanding.length === 0 ? (
            <p className="text-sm text-ink/50 py-4">No outstanding invoices. You're all caught up.</p>
          ) : (
            <ul className="space-y-3">
              {outstanding.map((inv) => (
                <li key={inv.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-ink">${inv.total_amount.toFixed(2)}</p>
                    <p className="text-xs text-ink/50">${(inv.total_amount - inv.amount_paid).toFixed(2)} due</p>
                  </div>
                  <StatusBadge status={inv.status} />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
