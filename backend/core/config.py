import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


_load_local_env()


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

    agent_use_real_llm: bool = _get_bool("AGENT_USE_REAL_LLM", True)
    openclaw_command: str = os.getenv("OPENCLAW_COMMAND", DEFAULT_OPENCLAW_COMMAND)
    openclaw_timeout_seconds: int = int(os.getenv("OPENCLAW_TIMEOUT_SECONDS", "120"))
    openclaw_thinking: str = os.getenv("OPENCLAW_THINKING", "minimal")
    openclaw_agent_collect: str = os.getenv("OPENCLAW_AGENT_COLLECT", "tender-collect")
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
    discovery_source_enabled_ggzy: bool = _get_bool("DISCOVERY_SOURCE_ENABLED_GGZY", True)
    discovery_collect_use_openclaw_agent: bool = _get_bool(
        "DISCOVERY_COLLECT_USE_OPENCLAW_AGENT",
        True,
    )
    discovery_collect_use_real_ggzy: bool = _get_bool("DISCOVERY_COLLECT_USE_REAL_GGZY", True)
    discovery_ggzy_list_url: str = os.getenv("DISCOVERY_GGZY_LIST_URL", "https://www.ggzy.gov.cn/")
    discovery_ggzy_max_projects: int = int(os.getenv("DISCOVERY_GGZY_MAX_PROJECTS", "5"))
    discovery_ggzy_timeout_seconds: int = int(os.getenv("DISCOVERY_GGZY_TIMEOUT_SECONDS", "8"))
    discovery_ggzy_budget_seconds: int = int(os.getenv("DISCOVERY_GGZY_BUDGET_SECONDS", "95"))
    discovery_ggzy_detail_text_limit: int = int(
        os.getenv("DISCOVERY_GGZY_DETAIL_TEXT_LIMIT", "2000")
    )

    project_root: Path = Path(__file__).resolve().parents[2]
    storage_root: Path = Path(__file__).resolve().parents[2] / "storage"

    @property
    def database_url(self) -> str:
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


settings = Settings()
