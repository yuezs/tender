import os
from dataclasses import dataclass
from pathlib import Path


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


DEFAULT_OPENCLAW_COMMAND = "openclaw.ps1" if os.name == "nt" else "openclaw"


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Tender Assistant")
    app_env: str = os.getenv("APP_ENV", "development")

    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "root")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "tender")

    agent_use_real_llm: bool = _get_bool("AGENT_USE_REAL_LLM", False)
    openclaw_command: str = os.getenv("OPENCLAW_COMMAND", DEFAULT_OPENCLAW_COMMAND)
    openclaw_timeout_seconds: int = int(os.getenv("OPENCLAW_TIMEOUT_SECONDS", "120"))
    openclaw_thinking: str = os.getenv("OPENCLAW_THINKING", "minimal")
    openclaw_agent_extract: str = os.getenv("OPENCLAW_AGENT_EXTRACT", "tender-extract")
    openclaw_agent_judge: str = os.getenv("OPENCLAW_AGENT_JUDGE", "tender-judge")
    openclaw_agent_generate: str = os.getenv("OPENCLAW_AGENT_GENERATE", "tender-generate")
    openclaw_model_default: str = os.getenv("OPENCLAW_MODEL_DEFAULT", "openai-codex/gpt-5.4")
    openclaw_state_dir: Path = Path(
        os.getenv("OPENCLAW_STATE_DIR", str(Path.home() / ".openclaw"))
    )
    openclaw_gateway_url: str = os.getenv("OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789")
    openclaw_gateway_token: str = os.getenv("OPENCLAW_GATEWAY_TOKEN", "").strip()
    openclaw_gateway_password: str = os.getenv("OPENCLAW_GATEWAY_PASSWORD", "").strip()

    project_root: Path = Path(__file__).resolve().parents[2]
    storage_root: Path = Path(__file__).resolve().parents[2] / "storage"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


settings = Settings()
