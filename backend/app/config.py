from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://fireuser:firepass@db:5432/firedb"
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()