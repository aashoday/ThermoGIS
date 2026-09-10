from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://fireuser:firepass@db:5432/firedb"
    environment: str = "development"
    firms_map_key: str = ""
    region_bbox: str = "68.1,20.1,74.5,24.7"

    class Config:
        env_file = ".env"

settings = Settings()