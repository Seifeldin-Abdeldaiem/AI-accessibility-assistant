from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    anthropic_api_key: str | None = None
    claude_model: str = "claude-sonnet-5"
    claude_vision_model: str = "claude-sonnet-5"

    # Soft spend guard. This is a rough estimate based on token usage, not a
    # hard billing control — set a real cap in your Anthropic console too.
    max_scan_spend_usd: float = 0.50

    # Leave unset to use Playwright's default browser cache location (set
    # this only if you installed Chromium to a custom path, e.g. the
    # pre-installed browser in some container images).
    playwright_browsers_path: str | None = None

    # Never set this to true in a deployment reachable from the internet.
    # It disables SSRF protection so localhost/private test pages can be
    # scanned during local development.
    allow_private_networks: bool = False

    scan_timeout_seconds: int = 45
    max_concurrent_scans: int = 2
    max_stored_reports: int = 50
    max_scans_per_ip_per_hour: int = 10
    max_violation_nodes_per_rule: int = 25
    max_groups_explained_by_claude: int = 20

    cors_origins: str = "http://localhost:3000"

    # Directory holding the exported frontend (Next.js `out/`). When set, the
    # backend serves the website too, so one service is the whole app.
    frontend_dir: str | None = None

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
