from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    subscription_period_days: int = 30
    trial_period_days: int = 7
    grace_period_days: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()