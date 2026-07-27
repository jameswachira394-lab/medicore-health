import { useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import { Card, Button, Input, Table, Banner, PageHeader } from "../../components/ui";

export default function AdminDoctors() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    user_id: "", full_name: "", specialization: "", department: "", license_number: "", years_experience: 0,
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setDoctors(await api.get("/doctors"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const addDoctor = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      await api.post("/doctors", { ...form, years_experience: Number(form.years_experience) });
      setSuccess(`Dr. ${form.full_name} added.`);
      setForm({ user_id: "", full_name: "", specialization: "", department: "", license_number: "", years_experience: 0 });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not add this doctor.");
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    { key: "full_name", header: "Name", render: (d) => `Dr. ${d.full_name}` },
    { key: "specialization", header: "Specialization" },
    { key: "department", header: "Department" },
    { key: "license_number", header: "License #" },
    { key: "years_experience", header: "Experience", render: (d) => `${d.years_experience} yrs` },
  ];

  return (
    <div>
      <PageHeader eyebrow="Care team" title="Doctors" description="Onboard new doctors and view the full directory." />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Add a doctor" className="lg:col-span-1">
          <form onSubmit={addDoctor} className="space-y-3">
            {error && <Banner tone="danger">{error}</Banner>}
            {success && <Banner tone="success">{success}</Banner>}
            <Input label="Linked user ID" required placeholder="From auth-service registration" value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} />
            <Input label="Full name" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <Input label="Specialization" required value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} />
            <Input label="Department" required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
            <Input label="License number" required value={form.license_number} onChange={(e) => setForm({ ...form, license_number: e.target.value })} />
            <Input label="Years of experience" type="number" min="0" value={form.years_experience} onChange={(e) => setForm({ ...form, years_experience: e.target.value })} />
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Adding…" : "Add doctor"}
            </Button>
          </form>
        </Card>

        <Card title="Directory" className="lg:col-span-2">
          {loading ? <p className="text-sm text-ink/40">Loading…</p> : <Table columns={columns} rows={doctors} emptyLabel="No doctors yet." />}
        </Card>
      </div>
    </div>
  );
}
