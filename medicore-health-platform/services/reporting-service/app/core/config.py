from shared_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "reporting-service"
    APPOINTMENT_SERVICE_URL: str = "http://appointment-service:8000"
    BILLING_SERVICE_URL: str = "http://billing-service:8000"
    PATIENT_SERVICE_URL: str = "http://patient-service:8000"
    DOCTOR_SERVICE_URL: str = "http://doctor-service:8000"


settings = Settings()
