# src/config/settings.py
"""配置文件"""

from typing import Optional


class Settings:
    """LLM 配置"""

    def __init__(
        self,
        model_name: str = "qwen3.5-0.8b",
        base_url: str = "http://127.0.0.1:1234/v1",
        api_key: str = "dummy",
    ) -> None:
        """初始化配置。

        Args:
            model_name: 模型名称
            base_url: LLM 服务地址
            api_key: API 密钥
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key


DEFAULT_SETTINGS = Settings()