from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Configuration
    FRONTEND_URL: str = "http://localhost:3000"

    # qwen3-vl-plus Configuration
    # DashScope API Key (从阿里云百炼获取，格式: sk-xxxxxxx)
    QWEN_API_KEY: str = ""
    # Qwen API 地址，默认使用阿里云官方地址
    QWEN_API_URL: Optional[str] = None
    # 模型名称：qwen3-vl-plus, qwen-vl-max 等
    QWEN_MODEL: str = "qwen3-vl-plus"

    # Storage Configuration
    STORAGE_PATH: str = "./storage"
    UPLOADS_DIR: str = "uploads"
    PROCESSED_DIR: str = "processed"
    THUMBNAILS_DIR: str = "thumbnails"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def uploads_path(self) -> str:
        return os.path.join(self.STORAGE_PATH, self.UPLOADS_DIR)

    @property
    def processed_path(self) -> str:
        return os.path.join(self.STORAGE_PATH, self.PROCESSED_DIR)

    @property
    def thumbnails_path(self) -> str:
        return os.path.join(self.STORAGE_PATH, self.THUMBNAILS_DIR)

    # Qwen Debug Configuration (调试配置)
    # 开启后可跳过 API 调用，使用本地 JSON 文件
    QWEN_DEBUG_MODE: bool = False
    QWEN_MOCK_RESPONSE_FILE: str = ""
    QWEN_SAVE_RESPONSE: bool = True
    QWEN_RESPONSE_DIR: str = "./debug_responses"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
