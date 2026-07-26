from shared_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "notification-service"
    AWS_SES_FROM_ADDRESS: str = "no-reply@medicore.health"
    AWS_SNS_REGION: str = "us-east-1"
    FCM_SERVER_KEY: str = ""


settings = Settings()
