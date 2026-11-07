from pydantic_settings import BaseSettings, SettingsConfigDict
import logging
import sys

class Settings(BaseSettings):
    # 這裡的變數名稱要對應 .env 裡的內容 (不分大小寫，但大寫比較標準)
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256" # 建議加上預設值
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    ) 


settings = Settings()


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO), 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("koko-ai-api")
logger.info("Logging is configured. Level: %s", settings.LOG_LEVEL)

_WEAK_SECRETS = {"changeme", "replace-with-openssl-rand-hex-32", "secret", "password"}
if settings.ALGORITHM != "HS256":
    raise RuntimeError("ALGORITHM 只支援 HS256")
if settings.SECRET_KEY.strip().lower() in _WEAK_SECRETS or len(settings.SECRET_KEY.strip()) < 32:
    secret_message = "SECRET_KEY 太弱。請在 .env 設成 openssl rand -hex 32 的結果。"
    if settings.DEBUG:
        logger.warning(secret_message)
    else:
        raise RuntimeError(secret_message)
