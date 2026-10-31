from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://qash:qash@localhost:5432/qash"
    database_url_test: str = "postgresql+psycopg://qash:qash@localhost:5433/qash_test"
    jwt_secreto: str = "cambiar-en-produccion"
    jwt_minutos: int = 30
    groq_api_key: str | None = None
    groq_modelo: str = "openai/gpt-oss-120b"
    ollama_url: str = "http://localhost:11434"
    ollama_modelo_embeddings: str = "nomic-embed-text"
    chroma_url: str = "http://localhost:8001"
    whisper_modelo: str = "small"
    archivos_dir: str = "/datos/archivos"
    cors_origenes: str = "http://localhost:5173"


settings = Settings()
