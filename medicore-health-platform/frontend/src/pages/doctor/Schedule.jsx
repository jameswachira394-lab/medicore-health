import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { Card, StatusBadge, Table, PageHeader, Button } from "../../components/ui";

export default function DoctorSchedule() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get("/appointments");
        setAppointments(data.sort((a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start)));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const columns = [
    {
      key: "when",
      header: "When",
      render: (a) => new Date(a.scheduled_start).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }),
    },
    { key: "patient", header: "Patient", render: (a) => a.patient_id.slice(0, 8) },
    { key: "reason", header: "Reason", render: (a) => a.reason || "—" },
    { key: "status", header: "Status", render: (a) => <StatusBadge status={a.status} /> },
    {
      key: "actions",
      header: "",
      render: (a) => (
        <Link to={`/doctor/patients/${a.patient_id}`}>
          <Button variant="ghost">Open chart</Button>
        </Link>
      ),
    },
  ];

  return (
    <div>
      <PageHeader eyebrow="All appointments" title="Schedule" description="Every appointment across all time periods." />
      <Card>{loading ? <p className="text-sm text-ink/40">Loading…</p> : <Table columns={columns} rows={appointments} emptyLabel="No appointments." />}</Card>
    </div>
  );
}
