from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


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
    # Checksums for integrity validation
    model_sha256: str = Field(
        default="2634be2a3377882d8d42e1e4f03e28e588af060f5c0dd7ffeac4366eccedb562",
        description="Expected SHA256 checksum of the model file",
    )
    config_sha256: str = Field(
        default="1ffb27b0ec53b269a9282e90b2d3d164c0f9b367d9291db28bd176a315fd8a3f",
        description="Expected SHA256 checksum of the config file",
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

    # Auth & Security
    api_key: str = Field(
        default="", description="Legacy single API Key support", repr=False
    )
    api_keys: List[str] = Field(
        default=[], description="List of valid API Keys for rotation", repr=False
    )
    audit_log_enabled: bool = Field(default=True)
    hmac_secret: str = Field(
        default="", description="Secret for HMAC signature verification", repr=False
    )
    hmac_enabled: bool = Field(
        default=False, description="Enforce HMAC signature on critical endpoints"
    )

    # Circuit Breaker
    breaker_enabled: bool = Field(default=True)
    breaker_failure_threshold: int = Field(default=5, ge=1)
    breaker_cooldown_seconds: int = Field(default=30, ge=1)

    # Cache Configuration
    prediction_cache_size: int = Field(
        default=10000, ge=100, description="LRU cache size for predictions"
    )

    # Auth Rate Limiting
    auth_rate_limit_max: int = Field(
        default=5, ge=1, description="Max auth attempts per window"
    )
    auth_rate_limit_window: int = Field(
        default=60, ge=1, description="Auth rate limit window in seconds"
    )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        """Validate security configuration and enforce best practices.

        This validator ensures:
        1. API keys are properly configured
        2. HMAC secrets meet minimum complexity requirements
        3. Security settings are consistent

        Returns:
            Validated settings instance

        Raises:
            ValueError: If security requirements are not met
        """
        # 1. API Keys Validation - Merge legacy single key with keys list
        if self.api_key and self.api_key not in self.api_keys:
            self.api_keys.append(self.api_key)

        # 2. HMAC Secret Validation - Enforce minimum complexity when enabled
        if self.hmac_enabled:
            if not self.hmac_secret:
                raise ValueError("HMAC is enabled but hmac_secret is missing")
            if len(self.hmac_secret) < 32:
                raise ValueError(
                    "HMAC secret must be at least 32 characters long for security"
                )

        return self


settings = Settings()
