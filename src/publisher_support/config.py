from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = ROOT_DIR / "scenarios"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    video_demo: bool = True
    demo_step_delay_ms: int = 800
    dry_run: bool = True
    auto_approve_delay_sec: float = 2.0
    openai_api_key: str = ""
    anthropic_api_key: str = ""


settings = Settings()
