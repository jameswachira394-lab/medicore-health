import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { Card, Button, StatusBadge, PageHeader, Banner } from "../../components/ui";

function isToday(iso) {
  const d = new Date(iso);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

export default function DoctorToday() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get("/appointments");
      setAppointments(data.filter((a) => isToday(a.scheduled_start)).sort((a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const confirm = async (id) => {
    setBusyId(id);
    setError("");
    try {
      await api.post(`/appointments/${id}/confirm`);
      await load();
    } catch (err) {
      setError(err.detail || "Could not confirm.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <PageHeader eyebrow="Today's schedule" title="Your patients today" description="Confirm requests and jump into a patient's chart." />
      {error && <div className="mb-4"><Banner tone="danger">{error}</Banner></div>}

      {loading ? (
        <p className="text-sm text-ink/40">Loading…</p>
      ) : appointments.length === 0 ? (
        <Card><p className="text-sm text-ink/50 py-6 text-center">No appointments scheduled for today.</p></Card>
      ) : (
        <div className="space-y-3">
          {appointments.map((a) => (
            <Card key={a.id} className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <p className="font-mono text-sm text-ink/60 w-16">
                  {new Date(a.scheduled_start).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
                </p>
                <div>
                  <p className="text-sm font-medium text-ink">Patient {a.patient_id.slice(0, 8)}</p>
                  <p className="text-xs text-ink/50">{a.reason || "General consultation"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={a.status} />
                {a.status === "requested" && (
                  <Button disabled={busyId === a.id} onClick={() => confirm(a.id)}>
                    {busyId === a.id ? "Confirming…" : "Confirm"}
                  </Button>
                )}
                <Link to={`/doctor/patients/${a.patient_id}`}>
                  <Button variant="ghost">Open chart</Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
