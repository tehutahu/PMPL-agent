"""LLM管理システム"""

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

import structlog
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from ..config.settings import LLMProviderConfig, Settings

logger = structlog.get_logger(__name__)


class LLMProvider(Enum):
    """LLMプロバイダー"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMModel(Enum):
    """LLMモデル"""
    # OpenAI
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_35_TURBO = "gpt-3.5-turbo"
    
    # Anthropic
    CLAUDE_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"


class LLMInterface(ABC):
    """LLMインターフェース"""
    
    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """テキスト生成"""
        pass
    
    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """ツール付きテキスト生成"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """モデル名"""
        pass


class OpenAILLM(LLMInterface):
    """OpenAI LLM実装"""
    
    def __init__(self, config: LLMProviderConfig, api_key: str):
        self.config = config
        self.client = AsyncOpenAI(api_key=api_key)
        self._model_name = config.model
    
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """テキスト生成"""
        try:
            response = await self.client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                timeout=self.config.timeout,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(
                "OpenAI API呼び出しエラー",
                error=str(e),
                model=self._model_name
            )
            raise
    
    async def generate_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """ツール付きテキスト生成"""
        try:
            response = await self.client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                timeout=self.config.timeout,
            )
            
            message = response.choices[0].message
            return {
                "content": message.content,
                "tool_calls": message.tool_calls,
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.error(
                "OpenAI API（ツール付き）呼び出しエラー",
                error=str(e),
                model=self._model_name
            )
            raise
    
    @property
    def model_name(self) -> str:
        return self._model_name


class AnthropicLLM(LLMInterface):
    """Anthropic LLM実装"""
    
    def __init__(self, config: LLMProviderConfig, api_key: str):
        self.config = config
        self.client = AsyncAnthropic(api_key=api_key)
        self._model_name = config.model
    
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """テキスト生成"""
        try:
            # Anthropic APIは system メッセージを分離する必要がある
            system_message = ""
            formatted_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    formatted_messages.append(msg)
            
            response = await self.client.messages.create(
                model=self._model_name,
                system=system_message,
                messages=formatted_messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens or 4000,
                timeout=self.config.timeout,
            )
            
            return response.content[0].text if response.content else ""
        except Exception as e:
            logger.error(
                "Anthropic API呼び出しエラー",
                error=str(e),
                model=self._model_name
            )
            raise
    
    async def generate_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """ツール付きテキスト生成"""
        try:
            # AnthropicのTool Useフォーマットに変換
            system_message = ""
            formatted_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    formatted_messages.append(msg)
            
            response = await self.client.messages.create(
                model=self._model_name,
                system=system_message,
                messages=formatted_messages,
                tools=tools,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens or 4000,
                timeout=self.config.timeout,
            )
            
            return {
                "content": response.content[0].text if response.content else "",
                "tool_calls": getattr(response, "tool_calls", None),
                "finish_reason": response.stop_reason,
            }
        except Exception as e:
            logger.error(
                "Anthropic API（ツール付き）呼び出しエラー",
                error=str(e),
                model=self._model_name
            )
            raise
    
    @property
    def model_name(self) -> str:
        return self._model_name


class LLMProviderInterface(ABC):
    """LLMプロバイダーインターフェース"""
    
    @abstractmethod
    def create_llm(self, config: LLMProviderConfig) -> LLMInterface:
        """LLMインスタンスを作成"""
        pass


class OpenAIProvider(LLMProviderInterface):
    """OpenAIプロバイダー"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def create_llm(self, config: LLMProviderConfig) -> LLMInterface:
        return OpenAILLM(config, self.api_key)


class AnthropicProvider(LLMProviderInterface):
    """Anthropicプロバイダー"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def create_llm(self, config: LLMProviderConfig) -> LLMInterface:
        return AnthropicLLM(config, self.api_key)


class LLMManager:
    """LLM管理システム"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.providers: Dict[LLMProvider, LLMProviderInterface] = {}
        self._llm_cache: Dict[str, LLMInterface] = {}
        
        # プロバイダーの初期化
        self._init_providers()
    
    def _init_providers(self) -> None:
        """LLMプロバイダーの初期化"""
        if self.settings.openai_api_key:
            self.providers[LLMProvider.OPENAI] = OpenAIProvider(
                self.settings.openai_api_key
            )
        
        if self.settings.anthropic_api_key:
            self.providers[LLMProvider.ANTHROPIC] = AnthropicProvider(
                self.settings.anthropic_api_key
            )
        
        logger.info(
            "LLMプロバイダー初期化完了",
            providers=list(self.providers.keys())
        )
    
    def get_llm(self, agent_name: str) -> LLMInterface:
        """エージェント用LLMインスタンス取得"""
        # キャッシュから取得
        if agent_name in self._llm_cache:
            return self._llm_cache[agent_name]
        
        # 設定を取得
        config = self.settings.get_agent_config(agent_name)
        
        # プロバイダーを取得
        provider_enum = LLMProvider(config.provider)
        if provider_enum not in self.providers:
            raise ValueError(f"プロバイダー '{config.provider}' が利用できません")
        
        provider = self.providers[provider_enum]
        
        # LLMインスタンスを作成
        llm = provider.create_llm(config)
        
        # キャッシュに保存
        self._llm_cache[agent_name] = llm
        
        logger.info(
            "LLMインスタンス作成",
            agent_name=agent_name,
            provider=config.provider,
            model=config.model
        )
        
        return llm
    
    def clear_cache(self) -> None:
        """LLMキャッシュをクリア"""
        self._llm_cache.clear()
        logger.info("LLMキャッシュをクリアしました")
    
    async def health_check(self) -> Dict[str, bool]:
        """各プロバイダーのヘルスチェック"""
        results = {}
        
        for provider_enum, provider in self.providers.items():
            try:
                # 簡単なテスト用LLMインスタンスを作成
                test_config = LLMProviderConfig(
                    provider=provider_enum.value,
                    model="gpt-3.5-turbo" if provider_enum == LLMProvider.OPENAI else "claude-3-haiku-20240307",
                    temperature=0.1,
                    max_tokens=10
                )
                
                llm = provider.create_llm(test_config)
                
                # 簡単なテストメッセージ
                test_messages = [{"role": "user", "content": "Hello"}]
                
                # タイムアウト付きでテスト
                await asyncio.wait_for(
                    llm.generate(test_messages),
                    timeout=10.0
                )
                
                results[provider_enum.value] = True
                
            except Exception as e:
                logger.warning(
                    "プロバイダーヘルスチェック失敗",
                    provider=provider_enum.value,
                    error=str(e)
                )
                results[provider_enum.value] = False
        
        return results 