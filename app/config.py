from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "predictive_maintenance"
    DB_USER: str = "iot_user"
    DB_PASSWORD: str = "iot_secret"
    API_KEY: str = "changeme"

    class Config:
        env_file = ".env"


settings = Settings()