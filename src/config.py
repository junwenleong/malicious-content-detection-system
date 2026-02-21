from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    model_path: str = Field(
        default="models/malicious_content_detector_calibrated.pkl",
        description="Path to the trained model file",
    )
    config_path: str = Field(
        default="models/malicious_content_detector_config.pkl",
        description="Path to the model configuration file",
    )
    model_version: str = Field(default="v1.0.0")
    decision_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="CORS allowed origins",
    )
    rate_limit_max: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    max_text_length: int = Field(default=10000, ge=1)
    max_batch_items: int = Field(default=1000, ge=1)
    max_csv_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    api_key: str = Field(default="")
    fastui_enabled: bool = Field(default=True)


settings = Settings()
