
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List
import os

load_dotenv()


class Settings(BaseSettings):
    
    APP_NAME: str = "Docet"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    LOCAL_STORAGE_PATH: str = "./data"
    
    VECTOR_DB_PATH: str = "./data/vector_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_STORAGE_BUCKET: str = ""
    GOOGLE_CLOUD_REGION: str = "us-central1"
    
    GOOGLE_AI_STUDIO_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    SECRET_KEY: str = "your-secret-key-here"
    JWT_SECRET: str = "your-jwt-secret-here"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)