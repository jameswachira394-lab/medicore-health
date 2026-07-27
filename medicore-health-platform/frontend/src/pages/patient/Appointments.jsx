import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Card, Button, StatusBadge, Table, PageHeader, Banner } from "../../components/ui";

export default function PatientAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get("/appointments");
      setAppointments(data.sort((a, b) => new Date(b.scheduled_start) - new Date(a.scheduled_start)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const cancel = async (id) => {
    setError("");
    setBusyId(id);
    try {
      await api.post(`/appointments/${id}/cancel`);
      await load();
    } catch (err) {
      setError(err.detail || "Could not cancel this appointment.");
    } finally {
      setBusyId(null);
    }
  };

  const columns = [
    {
      key: "when",
      header: "When",
      render: (a) => new Date(a.scheduled_start).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }),
    },
    { key: "reason", header: "Reason", render: (a) => a.reason || "—" },
    { key: "status", header: "Status", render: (a) => <StatusBadge status={a.status} /> },
    {
      key: "actions",
      header: "",
      render: (a) =>
        ["requested", "confirmed"].includes(a.status) ? (
          <Button variant="ghost" className="text-danger" disabled={busyId === a.id} onClick={() => cancel(a.id)}>
            {busyId === a.id ? "Cancelling…" : "Cancel"}
          </Button>
        ) : null,
    },
  ];

  return (
    <div>
      <PageHeader eyebrow="Your care" title="Appointments" description="Everything you've booked, past and upcoming." />
      {error && <div className="mb-4"><Banner tone="danger">{error}</Banner></div>}
      <Card>{loading ? <p className="text-sm text-ink/40">Loading…</p> : <Table columns={columns} rows={appointments} emptyLabel="No appointments yet." />}</Card>
    </div>
  );
}
