import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_BY_ROLE = {
  patient: [
    { to: "/patient", label: "Overview", end: true },
    { to: "/patient/find-a-doctor", label: "Find a doctor" },
    { to: "/patient/appointments", label: "Appointments" },
    { to: "/patient/records", label: "Medical records" },
    { to: "/patient/billing", label: "Billing" },
  ],
  doctor: [
    { to: "/doctor", label: "Today", end: true },
    { to: "/doctor/schedule", label: "Schedule" },
    { to: "/doctor/availability", label: "Availability" },
  ],
  hospital_admin: [
    { to: "/admin", label: "Overview", end: true },
    { to: "/admin/doctors", label: "Doctors" },
    { to: "/admin/reports", label: "Reports" },
  ],
  system_admin: [
    { to: "/admin", label: "Overview", end: true },
    { to: "/admin/doctors", label: "Doctors" },
    { to: "/admin/reports", label: "Reports" },
  ],
};

const ROLE_LABEL = {
  patient: "Patient",
  doctor: "Doctor",
  nurse: "Nurse",
  receptionist: "Receptionist",
  hospital_admin: "Hospital Admin",
  system_admin: "System Admin",
};

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = NAV_BY_ROLE[user?.role] || [];

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-canvas">
      <aside className="w-60 shrink-0 border-r border-line bg-surface flex flex-col">
        <div className="px-5 py-5 border-b border-line">
          <p className="font-display text-lg text-brand-dim tracking-tight">MediCore</p>
          <p className="text-xs text-ink/45 mt-0.5">Health Platform</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-brand-tint text-brand-dim" : "text-ink/65 hover:bg-canvas hover:text-ink"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-3 py-4 border-t border-line">
          <button
            onClick={handleLogout}
            className="w-full text-left rounded-lg px-3 py-2 text-sm font-medium text-ink/60 hover:bg-canvas hover:text-danger transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-line bg-surface flex items-center justify-end px-6 gap-3">
          <span className="text-xs font-mono text-ink/40">{user?.email}</span>
          <span className="inline-flex items-center rounded-full bg-brand-tint text-brand-dim text-xs font-medium px-2.5 py-1">
            {ROLE_LABEL[user?.role] || user?.role}
          </span>
        </header>
        <main className="flex-1 p-8 max-w-6xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
