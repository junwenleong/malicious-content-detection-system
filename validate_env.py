#!/usr/bin/env python3
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def validate_env() -> int:
    """Validate environment variables against configuration."""
    print("🔍 Validating environment configuration...")

    # Load .env file
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  No .env file found. Using default/environment variables.")
    else:
        load_dotenv()
        print(f"✅ Loaded .env from {env_path.absolute()}")

    try:
        from src.config import settings

        print("\n✅ Configuration loaded successfully!")

        # Check critical paths
        model_path = Path(settings.model_path)
        if not model_path.exists():
            print(f"⚠️  Warning: Model file not found at {model_path}")
            print("   (This is expected during CI/CD or before training)")
        else:
            print(f"✅ Model file found: {model_path}")

        # Print summary (masking secrets)
        print("\n📋 Current Configuration:")
        print(f"   - Model Version: {settings.model_version}")

        # Security validation
        security_warnings = []

        if not settings.api_key and not settings.api_keys:
            security_warnings.append(
                "❌ API Key: Not Set (CRITICAL: Inference will fail)"
            )
        elif settings.api_key:
            print(f"   - API Key: {'*' * 8}")
        else:
            print(f"   - API Keys: {len(settings.api_keys)} configured")

        if settings.hmac_enabled and not settings.hmac_secret:
            security_warnings.append(
                "❌ HMAC Secret: Enabled but not set (CRITICAL: HMAC verification will fail)"
            )
        elif settings.hmac_secret and len(settings.hmac_secret) < 32:
            security_warnings.append("⚠️  HMAC Secret: Weak (less than 32 characters)")

        # Check for insecure defaults
        if "*" in settings.allowed_origins:
            security_warnings.append("⚠️  CORS: Overly permissive ('*') in development")

        print(
            f"   - Rate Limit: {settings.rate_limit_max}/{settings.rate_limit_window}s"
        )
        print(
            f"   - Circuit Breaker: {'Enabled' if settings.breaker_enabled else 'Disabled'}"
        )
        print(f"   - CORS Origins: {settings.allowed_origins}")

        # Display security warnings
        if security_warnings:
            print("\n🔒 SECURITY WARNINGS:")
            for warning in security_warnings:
                print(f"   {warning}")

        return 0

    except Exception as e:
        print(f"\n❌ Configuration Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(validate_env())
