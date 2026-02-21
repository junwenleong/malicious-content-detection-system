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
        default="471da9faad5ab5ddc6687761bcd15fe626c6a75d0d0e36d829aeceb4bee2560d",
        description="Expected SHA256 checksum of the model file",
    )
    config_sha256: str = Field(
        default="ef686fd621ad7eb702eb4273c51ad1835a9565abb75e0aeaa0fcae6a4958e431",
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
    api_key: str = Field(default="", description="Legacy single API Key support")
    api_keys: List[str] = Field(default=[], description="List of valid API Keys for rotation")
    audit_log_enabled: bool = Field(default=True)
    hmac_secret: str = Field(default="", description="Secret for HMAC signature verification")
    hmac_enabled: bool = Field(default=False, description="Enforce HMAC signature on critical endpoints")
    
    # Circuit Breaker
    breaker_enabled: bool = Field(default=True)
    breaker_failure_threshold: int = Field(default=5, ge=1)
    breaker_cooldown_seconds: int = Field(default=30, ge=1)

    @model_validator(mode='after')
    def validate_security_settings(self) -> 'Settings':
        # 1. API Keys Validation
        if self.api_key and self.api_key not in self.api_keys:
            self.api_keys.append(self.api_key)
        
        # Enforce minimum complexity for secrets in production (implied by explicit check)
        # We'll just warn/check generally for now to avoid breaking existing dev setups hard, 
        # but for HMAC it's critical.
        if self.hmac_enabled:
            if not self.hmac_secret:
                 raise ValueError("HMAC is enabled but hmac_secret is missing")
            if len(self.hmac_secret) < 32:
                 # In a real strict environment, raise ValueError. 
                 # Here we might just want to ensure it's not trivial if we could log, 
                 # but Pydantic validators are for strict validation.
                 # Let's enforce 32 chars for HMAC if enabled.
                 raise ValueError("HMAC secret must be at least 32 characters long for security")
        
        return self


settings = Settings()
