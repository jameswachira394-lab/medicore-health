from pydantic import BaseModel


class DailyMetricsOut(BaseModel):
    metric_date: str
    active_patients: int
    appointments_total: int
    appointments_completed: int
    appointments_cancelled: int
    revenue: float

    class Config:
        from_attributes = True


class DoctorWorkloadOut(BaseModel):
    doctor_id: str
    appointment_count: int
