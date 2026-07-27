import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Card, PageHeader } from "../../components/ui";

export default function PatientRecords() {
  const { user } = useAuth();
  const [entries, setEntries] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [history, rx] = await Promise.all([
          api.get(`/medical-records/patients/${user.id}/history`),
          api.get(`/medical-records/patients/${user.id}/prescriptions`),
        ]);
        setEntries(history);
        setPrescriptions(rx);
      } finally {
        setLoading(false);
      }
    })();
  }, [user.id]);

  const rxByEntry = prescriptions.reduce((acc, rx) => {
    (acc[rx.record_entry_id] ||= []).push(rx);
    return acc;
  }, {});

  return (
    <div>
      <PageHeader eyebrow="Your health" title="Medical records" description="Diagnoses, treatment notes, and prescriptions from your care team." />
      {loading ? (
        <p className="text-sm text-ink/40">Loading…</p>
      ) : entries.length === 0 ? (
        <Card><p className="text-sm text-ink/50 py-4 text-center">No medical history recorded yet.</p></Card>
      ) : (
        <div className="space-y-4">
          {entries.map((e) => (
            <Card key={e.id}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-display text-lg text-ink">{e.diagnosis}</p>
                  <p className="text-xs text-ink/45 mt-0.5">
                    {new Date(e.created_at).toLocaleDateString(undefined, { dateStyle: "medium" })}
                  </p>
                </div>
              </div>
              {e.treatment && (
                <p className="text-sm text-ink/70 mt-3"><span className="font-medium text-ink/85">Treatment: </span>{e.treatment}</p>
              )}
              {e.notes && (
                <p className="text-sm text-ink/70 mt-1"><span className="font-medium text-ink/85">Notes: </span>{e.notes}</p>
              )}
              {rxByEntry[e.id]?.length > 0 && (
                <div className="mt-4 border-t border-line pt-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-ink/45 mb-2">Prescriptions</p>
                  <ul className="space-y-1.5">
                    {rxByEntry[e.id].map((rx) => (
                      <li key={rx.id} className="text-sm text-ink/75">
                        <span className="font-medium text-ink">{rx.medication}</span> — {rx.dosage}
                        {rx.instructions && <span className="text-ink/50"> · {rx.instructions}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
