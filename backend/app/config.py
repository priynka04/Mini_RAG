from pydantic import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    QDRANT_URL: str | None = None
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "documents"

    class Config:
        env_file = ".env"


settings = Settings()
