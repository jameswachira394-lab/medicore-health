import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Card, Button, Input, Banner, PageHeader } from "../../components/ui";

export default function PatientChart() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({ diagnosis: "", treatment: "", notes: "" });
  const [rxFor, setRxFor] = useState(null);
  const [rxForm, setRxForm] = useState({ medication: "", dosage: "", instructions: "" });
  const [labFor, setLabFor] = useState(null);
  const [labName, setLabName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setHistory(await api.get(`/medical-records/patients/${patientId}/history`));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not load this patient's history.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const addEntry = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("/medical-records/entries", {
        patient_id: patientId,
        doctor_id: user.id,
        diagnosis: form.diagnosis,
        treatment: form.treatment || undefined,
        notes: form.notes || undefined,
      });
      setForm({ diagnosis: "", treatment: "", notes: "" });
      setSuccess("Entry added to the patient's chart.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save this entry.");
    } finally {
      setSubmitting(false);
    }
  };

  const addPrescription = async (entryId) => {
    setSubmitting(true);
    setError("");
    try {
      await api.post("/medical-records/prescriptions", {
        record_entry_id: entryId,
        patient_id: patientId,
        doctor_id: user.id,
        ...rxForm,
      });
      setRxFor(null);
      setRxForm({ medication: "", dosage: "", instructions: "" });
      setSuccess("Prescription added.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save the prescription.");
    } finally {
      setSubmitting(false);
    }
  };

  const requestLab = async (entryId) => {
    setSubmitting(true);
    setError("");
    try {
      await api.post("/medical-records/lab-tests", {
        record_entry_id: entryId,
        patient_id: patientId,
        doctor_id: user.id,
        test_name: labName,
      });
      setLabFor(null);
      setLabName("");
      setSuccess("Lab test requested.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not request the lab test.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Patient chart"
        title={`Patient ${patientId.slice(0, 8)}`}
        action={<Button variant="ghost" onClick={() => navigate(-1)}>Back</Button>}
      />

      {error && <div className="mb-4"><Banner tone="danger">{error}</Banner></div>}
      {success && <div className="mb-4"><Banner tone="success">{success}</Banner></div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {loading ? (
            <p className="text-sm text-ink/40">Loading…</p>
          ) : history.length === 0 ? (
            <Card><p className="text-sm text-ink/50 py-6 text-center">No history yet — add the first entry.</p></Card>
          ) : (
            history.map((e) => (
              <Card key={e.id}>
                <p className="font-display text-lg text-ink">{e.diagnosis}</p>
                <p className="text-xs text-ink/45 mt-0.5">{new Date(e.created_at).toLocaleDateString(undefined, { dateStyle: "medium" })}</p>
                {e.treatment && <p className="text-sm text-ink/70 mt-3"><span className="font-medium text-ink/85">Treatment: </span>{e.treatment}</p>}
                {e.notes && <p className="text-sm text-ink/70 mt-1"><span className="font-medium text-ink/85">Notes: </span>{e.notes}</p>}

                <div className="flex gap-2 mt-4 border-t border-line pt-3">
                  <Button variant="ghost" onClick={() => setRxFor(rxFor === e.id ? null : e.id)}>+ Prescription</Button>
                  <Button variant="ghost" onClick={() => setLabFor(labFor === e.id ? null : e.id)}>+ Lab test</Button>
                </div>

                {rxFor === e.id && (
                  <div className="mt-3 space-y-2 bg-canvas rounded-lg p-3">
                    <Input label="Medication" value={rxForm.medication} onChange={(ev) => setRxForm({ ...rxForm, medication: ev.target.value })} />
                    <Input label="Dosage" value={rxForm.dosage} onChange={(ev) => setRxForm({ ...rxForm, dosage: ev.target.value })} />
                    <Input label="Instructions (optional)" value={rxForm.instructions} onChange={(ev) => setRxForm({ ...rxForm, instructions: ev.target.value })} />
                    <Button className="w-full" disabled={submitting || !rxForm.medication || !rxForm.dosage} onClick={() => addPrescription(e.id)}>
                      Save prescription
                    </Button>
                  </div>
                )}

                {labFor === e.id && (
                  <div className="mt-3 space-y-2 bg-canvas rounded-lg p-3">
                    <Input label="Test name" value={labName} onChange={(ev) => setLabName(ev.target.value)} />
                    <Button className="w-full" disabled={submitting || !labName} onClick={() => requestLab(e.id)}>
                      Request test
                    </Button>
                  </div>
                )}
              </Card>
            ))
          )}
        </div>

        <Card title="New chart entry">
          <form onSubmit={addEntry} className="space-y-4">
            <Input label="Diagnosis" required value={form.diagnosis} onChange={(e) => setForm({ ...form, diagnosis: e.target.value })} />
            <Input label="Treatment (optional)" value={form.treatment} onChange={(e) => setForm({ ...form, treatment: e.target.value })} />
            <label className="block">
              <span className="block text-sm font-medium text-ink/80 mb-1">Notes (optional, encrypted at rest)</span>
              <textarea
                className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink/40 focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand"
                rows={4}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </label>
            <Button type="submit" className="w-full" disabled={submitting || !form.diagnosis}>
              {submitting ? "Saving…" : "Add to chart"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
