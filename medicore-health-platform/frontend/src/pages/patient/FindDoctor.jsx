import { useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Card, Button, Input, Select, Banner, PageHeader } from "../../components/ui";

function nextWeekdayOptions() {
  // Generates the next 14 calendar days as bookable date options.
  return Array.from({ length: 14 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i + 1);
    return d;
  });
}

export default function FindDoctor() {
  const { user } = useAuth();
  const [specialization, setSpecialization] = useState("");
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [availability, setAvailability] = useState([]);
  const [form, setForm] = useState({ date: "", time: "", reason: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const search = async (q) => {
    setLoading(true);
    try {
      const results = await api.get(`/doctors${q ? `?specialization=${encodeURIComponent(q)}` : ""}`);
      setDoctors(results);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    search("");
  }, []);

  const openBooking = async (doctor) => {
    setSelected(doctor);
    setSuccess("");
    setError("");
    const slots = await api.get(`/doctors/${doctor.id}/availability`);
    setAvailability(slots);
  };

  const availableDays = new Set(availability.map((a) => a.day_of_week));
  const dateOptions = nextWeekdayOptions().filter((d) => availableDays.has((d.getDay() + 6) % 7));

  const onBook = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const start = new Date(`${form.date}T${form.time}:00`);
      const end = new Date(start.getTime() + 30 * 60000);
      await api.post("/appointments", {
        patient_id: user.id,
        doctor_id: selected.id,
        scheduled_start: start.toISOString(),
        scheduled_end: end.toISOString(),
        reason: form.reason || undefined,
      });
      setSuccess(`Appointment requested with Dr. ${selected.full_name} — you'll be notified once it's confirmed.`);
      setSelected(null);
      setForm({ date: "", time: "", reason: "" });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not book that slot. Try another time.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader eyebrow="Care team" title="Find a doctor" description="Search by specialty and request an appointment." />

      {success && <div className="mb-5"><Banner tone="success">{success}</Banner></div>}

      <div className="flex gap-3 mb-6 max-w-md">
        <Input
          placeholder="Search by specialization (e.g. Cardiology)"
          value={specialization}
          onChange={(e) => setSpecialization(e.target.value)}
          className="flex-1"
        />
        <Button onClick={() => search(specialization)}>Search</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          <p className="text-sm text-ink/40">Loading…</p>
        ) : doctors.length === 0 ? (
          <p className="text-sm text-ink/50">No doctors found for that search.</p>
        ) : (
          doctors.map((d) => (
            <Card key={d.id}>
              <p className="font-display text-lg text-ink">Dr. {d.full_name}</p>
              <p className="text-sm text-brand-dim">{d.specialization}</p>
              <p className="text-xs text-ink/50 mt-1">{d.department} · {d.years_experience} yrs experience</p>
              <Button variant="secondary" className="mt-4 w-full" onClick={() => openBooking(d)}>
                Request appointment
              </Button>
            </Card>
          ))
        )}
      </div>

      {selected && (
        <div className="fixed inset-0 bg-ink/30 flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-xl p-6 w-full max-w-sm border border-line">
            <p className="font-display text-lg text-ink mb-1">Book with Dr. {selected.full_name}</p>
            <p className="text-sm text-ink/50 mb-4">{selected.specialization}</p>
            <form onSubmit={onBook} className="space-y-4">
              {error && <Banner tone="danger">{error}</Banner>}
              <Select
                label="Date"
                required
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              >
                <option value="">Choose a date</option>
                {dateOptions.map((d) => (
                  <option key={d.toISOString()} value={d.toISOString().slice(0, 10)}>
                    {d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
                  </option>
                ))}
              </Select>
              <Input label="Time" type="time" required value={form.time} onChange={(e) => setForm({ ...form, time: e.target.value })} />
              <Input label="Reason for visit (optional)" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
              <div className="flex gap-2">
                <Button variant="ghost" type="button" className="flex-1" onClick={() => setSelected(null)}>Cancel</Button>
                <Button type="submit" className="flex-1" disabled={submitting}>{submitting ? "Booking…" : "Confirm request"}</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
