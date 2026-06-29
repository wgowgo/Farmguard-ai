from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 로컬 SQLite
    database_url: str = "sqlite+aiosqlite:///./farmguard.db"
    public_data_service_key: str = ""
    ncpms_api_key: str = ""
    nongsaro_api_key: str = ""
    demo_mode: bool = True
    openai_api_key: str = ""
    model_version: str = "v1.0"

    mvp_crop: str = "고추"
    mvp_pests: list[str] = ["탄저병", "역병", "담배나방"]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    class Config:
        env_file = ".env"


settings = Settings()
