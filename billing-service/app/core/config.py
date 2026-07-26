from shared_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "billing-service"
    PAYMENT_GATEWAY_API_KEY: str = ""


settings = Settings()
