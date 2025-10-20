"""Application configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application settings resolved from environment variables."""

    app_host: str = Field("0.0.0.0", description="FastAPI host binding")
    app_port: int = Field(8000, description="FastAPI port binding")
    debug: bool = Field(False, description="Enable debug mode")

    llm_provider: Literal["qwen", "deepseek", "openai"] = Field(
        "qwen", description="Active large language model provider"
    )
    qwen_api_key: str | None = Field(default=None, alias="QWEN_API_KEY")
    qwen_base_url: str | None = Field(default=None, alias="QWEN_BASE_URL")
    qwen_model: str | None = Field(default=None, alias="QWEN_MODEL")

    # Vision-Language 模型配置（用于图片识别）
    vl_enabled: bool = Field(default=True, alias="VL_ENABLED", description="启用 VL 模型进行图片识别")
    # MultiModalConversation 使用 qwen-vl-* 系列；使用 qwen-vl-plus 模型（更快更稳定）
    vl_model: str = Field(default="qwen-vl-plus", alias="VL_MODEL", description="VL 模型名称")
    vl_api_key: str | None = Field(default=None, alias="VL_API_KEY", description="VL 模型 API Key，默认使用 QWEN_API_KEY")
    vl_base_url: str | None = Field(default=None, alias="VL_BASE_URL", description="VL 模型 base URL")

    # 需求分析师专用配置
    analysis_agent_model: str = Field(default="qwen-max", alias="ANALYSIS_AGENT_MODEL")
    analysis_agent_api_key: str | None = Field(default=None, alias="ANALYSIS_AGENT_API_KEY")
    analysis_agent_base_url: str | None = Field(default=None, alias="ANALYSIS_AGENT_BASE_URL")

    # 测试工程师专用配置
    test_agent_model: str = Field(default="qwen-plus", alias="TEST_AGENT_MODEL")
    test_agent_api_key: str | None = Field(default=None, alias="TEST_AGENT_API_KEY")
    test_agent_base_url: str | None = Field(default=None, alias="TEST_AGENT_BASE_URL")

    # 质量评审专家专用配置
    review_agent_model: str = Field(default="qwen-plus", alias="REVIEW_AGENT_MODEL")
    review_agent_api_key: str | None = Field(default=None, alias="REVIEW_AGENT_API_KEY")
    review_agent_base_url: str | None = Field(default=None, alias="REVIEW_AGENT_BASE_URL")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./ai_requirement.db",
        description="SQLAlchemy database URL",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URI",
        alias="REDIS_URL",
    )
    session_ttl_hours: int = Field(
        default=72,
        ge=1,
        description="Session retention time in hours",
        alias="SESSION_TTL_HOURS",
    )
    session_cleanup_interval: int = Field(
        default=3600,
        ge=60,
        description="Background cleanup interval in seconds",
        alias="SESSION_CLEANUP_INTERVAL",
    )

    max_file_size: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum size (bytes) for uploaded documents",
        alias="MAX_FILE_SIZE",
    )
    upload_dir: Path = Field(
        default=Path("/tmp/uploads"),
        description="Upload directory",
        alias="UPLOAD_DIR",
    )
    llm_timeout: int = Field(default=120, alias="LLM_TIMEOUT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def session_ttl_seconds(self) -> int:
        """Return the session TTL in seconds."""

        return self.session_ttl_hours * 3600

    @property
    def resolved_upload_dir(self) -> Path:
        """Ensure upload directory exists and return absolute path."""

        path = Path(self.upload_dir).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_agent_config(self, agent_type: Literal["analysis", "test", "review"]) -> dict:
        """获取指定智能体的模型配置，支持 fallback 到默认 Qwen 配置."""

        config_map = {
            "analysis": (
                self.analysis_agent_model,
                self.analysis_agent_api_key,
                self.analysis_agent_base_url,
            ),
            "test": (
                self.test_agent_model,
                self.test_agent_api_key,
                self.test_agent_base_url,
            ),
            "review": (
                self.review_agent_model,
                self.review_agent_api_key,
                self.review_agent_base_url,
            ),
        }

        model, api_key, base_url = config_map[agent_type]

        return {
            "model": model or self.qwen_model or "qwen-plus",
            "api_key": api_key or self.qwen_api_key,
            "base_url": base_url or self.qwen_base_url,
        }

    def get_vl_config(self) -> dict:
        """获取 VL 模型配置."""
        return {
            "enabled": self.vl_enabled,
            "model": self.vl_model,
            "api_key": self.vl_api_key or self.qwen_api_key,
            "base_url": self.vl_base_url or self.qwen_base_url,
        }


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""

    return Settings()


settings = get_settings()
