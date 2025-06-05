"""基本テストケース"""

import pytest
from datetime import datetime

from pmpl_agent_system.models.data import (
    DiscussionSession,
    DiscussionStatus,
    PersonaStatement,
    DiscussionRound,
)
from pmpl_agent_system.config.settings import Settings, LLMProviderConfig


class TestDataModels:
    """データモデルのテスト"""
    
    def test_discussion_session_creation(self):
        """DiscussionSessionの作成テスト"""
        session = DiscussionSession(
            topic="テストトピック",
            organization_context={"company_size": 30}
        )
        
        assert session.topic == "テストトピック"
        assert session.organization_context["company_size"] == 30
        assert session.status == DiscussionStatus.INITIALIZED
        assert len(session.session_id) > 0
        assert isinstance(session.created_at, datetime)
    
    def test_persona_statement_creation(self):
        """PersonaStatementの作成テスト"""
        statement = PersonaStatement(
            persona_name="田中俊介",
            persona_role="ITスタートアップPM",
            statement="スタートアップでは人材確保が最大の課題です。",
            identified_issues=["採用競争の激化", "給与水準の制約"],
            proposed_solutions=["リモートワーク導入", "ストックオプション活用"],
            llm_model="gpt-4o"
        )
        
        assert statement.persona_name == "田中俊介"
        assert statement.persona_role == "ITスタートアップPM"
        assert len(statement.identified_issues) == 2
        assert len(statement.proposed_solutions) == 2
        assert isinstance(statement.timestamp, datetime)
    
    def test_discussion_round_operations(self):
        """DiscussionRoundの操作テスト"""
        round_data = DiscussionRound(
            round_id=1,
            participants=["startup_pm", "enterprise_pm"]
        )
        
        # 発言追加
        statement = PersonaStatement(
            persona_name="田中俊介",
            persona_role="ITスタートアップPM",
            statement="テスト発言",
            llm_model="gpt-4o"
        )
        
        round_data.add_statement(statement)
        
        assert len(round_data.statements) == 1
        assert round_data.statements[0] == statement
        
        # ラウンド完了
        round_data.complete_round()
        assert round_data.completed_at is not None


class TestSettings:
    """設定管理のテスト"""
    
    def test_llm_provider_config_creation(self):
        """LLMProviderConfigの作成テスト"""
        config = LLMProviderConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.timeout == 30  # デフォルト値
    
    def test_settings_creation(self):
        """Settingsの作成テスト"""
        settings = Settings()
        
        # デフォルト値の確認
        assert settings.default_llm.provider == "openai"
        assert settings.default_llm.model == "gpt-4o"
        assert settings.discussion.max_rounds == 3
        assert settings.storage.type == "local"
    
    def test_agent_config_retrieval(self):
        """エージェント設定取得のテスト"""
        settings = Settings()
        
        # デフォルト設定の取得
        default_config = settings.get_agent_config("unknown_agent")
        assert default_config == settings.default_llm
        
        # エージェント別設定がある場合のテスト
        # （実際の設定は個別に追加する必要がある）


if __name__ == "__main__":
    pytest.main([__file__]) 