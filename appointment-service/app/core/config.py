from shared_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "appointment-service"
    DOCTOR_SERVICE_URL: str = "http://doctor-service:8000"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"
    BILLING_SERVICE_URL: str = "http://billing-service:8000"


settings = Settings()
