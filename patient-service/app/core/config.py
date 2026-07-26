from shared_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "patient-service"


settings = Settings()
