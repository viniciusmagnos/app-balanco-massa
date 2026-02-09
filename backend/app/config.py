from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    upload_dir: Path = Path("/tmp/uploads")
    converted_dir: Path = Path("/tmp/converted")
    results_dir: Path = Path("/tmp/results")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
