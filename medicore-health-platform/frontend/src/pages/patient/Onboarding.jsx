import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Button, Input, Select, Banner, PageHeader } from "../../components/ui";

export default function Onboarding() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    date_of_birth: "",
    gender: "female",
    phone: "",
    address: "",
    emergency_contact: "",
    insurance_details: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("/patients", {
        user_id: user.id,
        full_name: user.full_name,
        email: user.email,
        ...form,
      });
      navigate("/patient", { replace: true });
    } catch (err) {
      setError(err.detail || "Could not save your profile.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <PageHeader
          eyebrow="One last step"
          title="Complete your patient profile"
          description="This information helps clinicians reach you and understand your care context. It's encrypted at rest."
        />
        <form onSubmit={onSubmit} className="bg-surface border border-line rounded-xl p-6 space-y-4">
          {error && <Banner tone="danger">{error}</Banner>}
          <Input
            label="Date of birth"
            type="date"
            required
            value={form.date_of_birth}
            onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
          />
          <Select
            label="Gender"
            value={form.gender}
            onChange={(e) => setForm({ ...form, gender: e.target.value })}
          >
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </Select>
          <Input
            label="Phone number"
            required
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
          <Input
            label="Address"
            required
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
          />
          <Input
            label="Emergency contact"
            placeholder="Name and phone number"
            value={form.emergency_contact}
            onChange={(e) => setForm({ ...form, emergency_contact: e.target.value })}
          />
          <Input
            label="Insurance details (optional)"
            value={form.insurance_details}
            onChange={(e) => setForm({ ...form, insurance_details: e.target.value })}
          />
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Saving…" : "Save and continue"}
          </Button>
        </form>
      </div>
    </div>
  );
}
