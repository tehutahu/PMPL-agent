"""設定管理システム"""

import os
from typing import Any, Dict, Optional
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMProviderConfig(BaseModel):
    """LLMプロバイダー設定"""
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    timeout: int = Field(default=30, gt=0)
    retry_count: int = Field(default=3, ge=0)


class AgentConfig(BaseModel):
    """エージェント設定"""
    llm: LLMProviderConfig


class DiscussionConfig(BaseModel):
    """議論システム設定"""
    max_rounds: int = Field(default=3, ge=1, le=5)
    sufficiency_threshold: float = Field(default=75.0, ge=0.0, le=100.0)
    timeout_minutes: int = Field(default=30, gt=0)


class StorageConfig(BaseModel):
    """ストレージ設定"""
    type: str = Field(default="local", pattern="^(local|database)$")
    path: str = "./data/discussions"


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # API設定
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(
        default=None, alias="ANTHROPIC_API_KEY"
    )
    
    # システム設定
    default_llm: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    
    # エージェント設定
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    
    # 議論設定
    discussion: DiscussionConfig = Field(default_factory=DiscussionConfig)
    
    # ストレージ設定
    storage: StorageConfig = Field(default_factory=StorageConfig)
    
    # ログ設定
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # API キーなどの追加フィールドを許可
    
    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Settings":
        """YAMLファイルから設定を読み込み"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        
        return cls(**yaml_data)
    
    def get_agent_config(self, agent_name: str) -> LLMProviderConfig:
        """エージェント別のLLM設定を取得"""
        if agent_name in self.agents:
            return self.agents[agent_name].llm
        return self.default_llm
    
    def validate_api_keys(self) -> None:
        """必要なAPIキーが設定されているかチェック"""
        if not self.openai_api_key and self.default_llm.provider == "openai":
            raise ValueError("OpenAI APIキーが設定されていません")
        
        if not self.anthropic_api_key and self.default_llm.provider == "anthropic":
            raise ValueError("Anthropic APIキーが設定されていません")


def load_default_config() -> Settings:
    """デフォルト設定を含む設定を読み込み"""
    # 環境変数から設定を読み込み
    settings = Settings()
    
    # デフォルト設定ファイルが存在する場合は読み込み
    default_config_path = Path("config/default.yaml")
    if default_config_path.exists():
        try:
            yaml_settings = Settings.from_yaml(default_config_path)
            # 環境変数設定を保持しつつYAML設定をマージ
            settings = Settings(
                **{
                    **yaml_settings.model_dump(),
                    "openai_api_key": settings.openai_api_key or yaml_settings.openai_api_key,
                    "anthropic_api_key": settings.anthropic_api_key or yaml_settings.anthropic_api_key,
                }
            )
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
    
    return settings 