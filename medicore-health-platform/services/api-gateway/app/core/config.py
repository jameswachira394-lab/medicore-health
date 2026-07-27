from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "api-gateway"

    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    PATIENT_SERVICE_URL: str = "http://patient-service:8000"
    DOCTOR_SERVICE_URL: str = "http://doctor-service:8000"
    APPOINTMENT_SERVICE_URL: str = "http://appointment-service:8000"
    MEDICAL_RECORDS_SERVICE_URL: str = "http://medical-records-service:8000"
    BILLING_SERVICE_URL: str = "http://billing-service:8000"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"
    REPORTING_SERVICE_URL: str = "http://reporting-service:8000"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()

# Maps the first path segment of an incoming request to the upstream
# service that owns it. This is the single entry point the frontend talks
# to, matching the "API Gateway" layer in the platform architecture — the
# frontend never needs to know individual service hostnames/ports.
ROUTE_MAP = {
    "auth": settings.AUTH_SERVICE_URL,
    "patients": settings.PATIENT_SERVICE_URL,
    "doctors": settings.DOCTOR_SERVICE_URL,
    "appointments": settings.APPOINTMENT_SERVICE_URL,
    "medical-records": settings.MEDICAL_RECORDS_SERVICE_URL,
    "billing": settings.BILLING_SERVICE_URL,
    "notifications": settings.NOTIFICATION_SERVICE_URL,
    "reports": settings.REPORTING_SERVICE_URL,
}
