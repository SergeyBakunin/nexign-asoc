from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://asoc:asoc@db:5432/asoc"
    api_token: str = "changeme"
    app_title: str = "Nexign ASOC"

    class Config:
        env_file = ".env"


settings = Settings()
