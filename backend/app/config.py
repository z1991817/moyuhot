from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Moyu API"
    app_env: str = "development"
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:4321", "http://127.0.0.1:4321"]
    )

    seesea_base_url: str = "http://127.0.0.1:18080"
    cn_market_scheduler_enabled: bool = False
    seesea_default_platforms: list[str] = Field(
        default_factory=lambda: [
            "weibo",
            "douyin",
            "kuaishou",
            "bilibili-hot-search",
            "douban",
            "hupu",
            "v2ex",
            "baidu",
            "linux-do",
            "toutiao",
            "thepaper",
            "ifeng",
            "tencent-hot",
            "wallstreetcn-hot",
            "cls-hot",
            "jin10",
            "gelonghui",
            "xueqiu-hotstock",
            "github-trending-today",
            "hackernews",
            "producthunt",
            "juejin",
            "sspai",
            "ithome",
            "coolapk",
            "nowcoder",
            "freebuf",
            "steam",
            "zhihu",
            "tieba",
            "36kr-renqi",
        ]
    )

    cache_db_path: str = "data/cache.db"
    home_cache_ttl_seconds: int = 60
    trends_cache_ttl_seconds: int = 300
    sources_cache_ttl_seconds: int = 600
    market_open_cache_ttl_seconds: int = 180
    market_closed_cache_ttl_seconds: int = 1800

    market_disclaimer: str = "仅供信息展示，不构成投资建议"
    public_site_url: str = "https://moyu.example.com"

    chat_gateway_base_url: str = "https://api.freetheai.xyz/v1"
    chat_gateway_api_key: str = ""
    chat_gateway_default_model: str = "fee/deepseek-v4-pro"
    chat_gateway_models: str = (
        "fee/deepseek-v4-pro,fee/kimi-k2.6,opc/qwen3.6-plus-free,"
        "glm/glm-5,glm/glm-5.1,opc/minimax-m3-free,bbl/gpt-5.4-mini"
    )
    chat_gateway_web_search_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
