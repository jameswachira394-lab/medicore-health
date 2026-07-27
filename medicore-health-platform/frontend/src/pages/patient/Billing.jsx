import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Card, Button, Select, StatusBadge, Banner, PageHeader } from "../../components/ui";

export default function PatientBilling() {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [payingId, setPayingId] = useState(null);
  const [method, setMethod] = useState("card");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setInvoices(await api.get(`/billing/patients/${user.id}/invoices`));
    } finally {
      setLoading(false);
    }
  }, [user.id]);

  useEffect(() => {
    load();
  }, [load]);

  const pay = async (invoice) => {
    setError("");
    setSubmitting(true);
    try {
      await api.post(`/billing/invoices/${invoice.id}/payments`, {
        amount: invoice.total_amount - invoice.amount_paid,
        method,
      });
      setPayingId(null);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Payment failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader eyebrow="Your account" title="Billing" description="Invoices from your visits and lab work." />
      {error && <div className="mb-4"><Banner tone="danger">{error}</Banner></div>}

      {loading ? (
        <p className="text-sm text-ink/40">Loading…</p>
      ) : invoices.length === 0 ? (
        <Card><p className="text-sm text-ink/50 py-4 text-center">No invoices yet.</p></Card>
      ) : (
        <div className="space-y-4">
          {invoices.map((inv) => {
            const due = inv.total_amount - inv.amount_paid;
            return (
              <Card key={inv.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-display text-lg text-ink">${inv.total_amount.toFixed(2)}</p>
                    <p className="text-xs text-ink/45 mt-0.5">{new Date(inv.created_at).toLocaleDateString(undefined, { dateStyle: "medium" })}</p>
                  </div>
                  <StatusBadge status={inv.status} />
                </div>
                <ul className="mt-3 text-sm text-ink/70 space-y-1">
                  {inv.line_items.map((li) => (
                    <li key={li.id} className="flex justify-between">
                      <span>{li.description}</span>
                      <span>${li.amount.toFixed(2)}</span>
                    </li>
                  ))}
                </ul>
                {due > 0 && (
                  <div className="mt-4 border-t border-line pt-3">
                    {payingId === inv.id ? (
                      <div className="flex items-end gap-2">
                        <Select label="Payment method" value={method} onChange={(e) => setMethod(e.target.value)} className="flex-1">
                          <option value="card">Card</option>
                          <option value="mobile_money">Mobile money</option>
                          <option value="cash">Cash</option>
                          <option value="insurance">Insurance</option>
                        </Select>
                        <Button disabled={submitting} onClick={() => pay(inv)}>
                          {submitting ? "Paying…" : `Pay $${due.toFixed(2)}`}
                        </Button>
                        <Button variant="ghost" onClick={() => setPayingId(null)}>Cancel</Button>
                      </div>
                    ) : (
                      <Button variant="secondary" onClick={() => setPayingId(inv.id)}>Pay ${due.toFixed(2)}</Button>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
