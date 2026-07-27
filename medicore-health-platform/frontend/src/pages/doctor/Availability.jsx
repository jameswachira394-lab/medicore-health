import { useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Card, Button, Select, Input, Banner, PageHeader } from "../../components/ui";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function DoctorAvailability() {
  const { user } = useAuth();
  const [doctorId, setDoctorId] = useState(null);
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ day_of_week: 0, start_time: "09:00", end_time: "13:00" });
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const mine = await api.get("/doctors/me");
        setDoctorId(mine.id);
        setSlots(await api.get(`/doctors/${mine.id}/availability`));
      } catch {
        setNotFound(true);
      }
    })();
  }, [user.id]);

  const addSlot = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const created = await api.post(`/doctors/${doctorId}/availability`, {
        day_of_week: Number(form.day_of_week),
        start_time: `${form.start_time}:00`,
        end_time: `${form.end_time}:00`,
      });
      setSlots([...slots, created]);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save that block.");
    } finally {
      setSubmitting(false);
    }
  };

  if (notFound) {
    return (
      <div>
        <PageHeader eyebrow="Schedule" title="Availability" />
        <Banner tone="danger">
          No doctor profile is linked to your account yet. Ask a hospital admin to add you via the Admin → Doctors page.
        </Banner>
      </div>
    );
  }

  return (
    <div>
      <PageHeader eyebrow="Schedule" title="Availability" description="Recurring weekly blocks patients can book into." />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Add a weekly block">
          <form onSubmit={addSlot} className="space-y-4">
            {error && <Banner tone="danger">{error}</Banner>}
            <Select label="Day" value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}>
              {DAYS.map((d, i) => (
                <option key={d} value={i}>{d}</option>
              ))}
            </Select>
            <div className="flex gap-3">
              <Input label="Start" type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
              <Input label="End" type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
            </div>
            <Button type="submit" className="w-full" disabled={submitting || !doctorId}>
              {submitting ? "Saving…" : "Add block"}
            </Button>
          </form>
        </Card>

        <Card title="Current schedule">
          {slots.length === 0 ? (
            <p className="text-sm text-ink/50 py-4">No recurring availability set yet.</p>
          ) : (
            <ul className="space-y-2">
              {slots
                .sort((a, b) => a.day_of_week - b.day_of_week)
                .map((s) => (
                  <li key={s.id} className="flex justify-between text-sm text-ink/75 border-b border-line/60 last:border-0 py-2">
                    <span className="font-medium text-ink">{DAYS[s.day_of_week]}</span>
                    <span>{s.start_time.slice(0, 5)}–{s.end_time.slice(0, 5)}</span>
                  </li>
                ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
