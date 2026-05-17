from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_api_key: str = ""
    llm_base_url: str | None = None
    llm_temperature: float = 0.3

    # Storage
    data_dir: Path = Path("data")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def profile_dir(self) -> Path:
        return self.data_dir / "profile"

    @property
    def resumes_dir(self) -> Path:
        return self.data_dir / "resumes"

    @property
    def history_db_path(self) -> Path:
        return self.data_dir / "history.db"

    model_config = {"env_file": ".env", "env_prefix": "IRESUME_"}


settings = Settings()
