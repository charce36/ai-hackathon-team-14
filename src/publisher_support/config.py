from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = ROOT_DIR / "scenarios"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore", env_ignore_empty=True)

    video_demo: bool = True
    demo_step_delay_ms: int = 800
    auto_approve_delay_sec: float = 2.0
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 2048
    rca_confidence_threshold: float = 0.6


settings = Settings()
