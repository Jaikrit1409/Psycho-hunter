from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENAI_API_KEY: str = Field(default="")
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://psycho_hunter:psycho_hunter_dev@localhost:5432/psycho_hunter"
    )


settings = Settings()
