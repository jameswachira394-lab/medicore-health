import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./layouts/AppLayout";

import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";

import Onboarding from "./pages/patient/Onboarding";
import PatientOverview from "./pages/patient/Overview";
import FindDoctor from "./pages/patient/FindDoctor";
import PatientAppointments from "./pages/patient/Appointments";
import PatientRecords from "./pages/patient/Records";
import PatientBilling from "./pages/patient/Billing";

import DoctorToday from "./pages/doctor/Today";
import DoctorSchedule from "./pages/doctor/Schedule";
import DoctorAvailability from "./pages/doctor/Availability";
import PatientChart from "./pages/doctor/PatientChart";

import AdminOverview from "./pages/admin/Overview";
import AdminDoctors from "./pages/admin/Doctors";
import AdminReports from "./pages/admin/Reports";

const HOME_BY_ROLE = {
  patient: "/patient",
  doctor: "/doctor",
  nurse: "/doctor",
  receptionist: "/admin",
  hospital_admin: "/admin",
  system_admin: "/admin",
};

function RoleHome() {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-ink/50 text-sm">Loading…</div>;
  }
  return <Navigate to={user ? HOME_BY_ROLE[user.role] || "/login" : "/login"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/patient/onboarding"
          element={
            <ProtectedRoute roles={["patient"]}>
              <Onboarding />
            </ProtectedRoute>
          }
        />

        <Route
          path="/patient"
          element={
            <ProtectedRoute roles={["patient"]}>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<PatientOverview />} />
          <Route path="find-a-doctor" element={<FindDoctor />} />
          <Route path="appointments" element={<PatientAppointments />} />
          <Route path="records" element={<PatientRecords />} />
          <Route path="billing" element={<PatientBilling />} />
        </Route>

        <Route
          path="/doctor"
          element={
            <ProtectedRoute roles={["doctor", "nurse"]}>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DoctorToday />} />
          <Route path="schedule" element={<DoctorSchedule />} />
          <Route path="availability" element={<DoctorAvailability />} />
          <Route path="patients/:patientId" element={<PatientChart />} />
        </Route>

        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={["receptionist", "hospital_admin", "system_admin"]}>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminOverview />} />
          <Route path="doctors" element={<AdminDoctors />} />
          <Route path="reports" element={<AdminReports />} />
        </Route>

        <Route path="/" element={<RoleHome />} />
        <Route path="*" element={<RoleHome />} />
      </Routes>
    </AuthProvider>
  );
}
