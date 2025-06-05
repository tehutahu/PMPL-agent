"""データモデル定義"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DiscussionStatus(Enum):
    """議論状態"""
    INITIALIZED = "initialized"
    ROUND1_IN_PROGRESS = "round1_in_progress"
    JUDGING = "judging"
    ROUND2_IN_PROGRESS = "round2_in_progress"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueCategory(Enum):
    """課題カテゴリ"""
    TALENT_MANAGEMENT = "talent_management"
    PROCESS_IMPROVEMENT = "process_improvement"
    ORGANIZATIONAL_SCALING = "organizational_scaling"


class IssuePriority(Enum):
    """課題優先度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PersonaStatement(BaseModel):
    """ペルソナの発言"""
    persona_name: str = Field(..., description="ペルソナ名")
    persona_role: str = Field(..., description="ペルソナの役職")
    statement: str = Field(..., description="発言内容")
    identified_issues: List[str] = Field(
        default_factory=list, description="特定した課題"
    )
    proposed_solutions: List[str] = Field(
        default_factory=list, description="提案した解決策"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="発言時刻")
    llm_model: str = Field(..., description="使用したLLMモデル")


class DiscussionRound(BaseModel):
    """議論ラウンド"""
    round_id: int = Field(..., description="ラウンドID", ge=1)
    participants: List[str] = Field(..., description="参加者一覧")
    statements: List[PersonaStatement] = Field(
        default_factory=list, description="発言一覧"
    )
    identified_issues: List[str] = Field(
        default_factory=list, description="このラウンドで特定された課題"
    )
    started_at: datetime = Field(
        default_factory=datetime.now, description="開始時刻"
    )
    completed_at: Optional[datetime] = Field(default=None, description="完了時刻")
    
    def add_statement(self, statement: PersonaStatement) -> None:
        """発言を追加"""
        self.statements.append(statement)
        if statement.identified_issues:
            self.identified_issues.extend(statement.identified_issues)
    
    def complete_round(self) -> None:
        """ラウンドを完了"""
        self.completed_at = datetime.now()


class SufficiencyJudgment(BaseModel):
    """課題十分性判定"""
    overall_score: float = Field(..., description="総合スコア", ge=0, le=100)
    coverage_analysis: Dict[str, float] = Field(
        ..., description="領域別カバレッジスコア"
    )
    missing_areas: List[str] = Field(
        default_factory=list, description="不足している領域"
    )
    recommended_personas: List[str] = Field(
        default_factory=list, description="推奨追加ペルソナ"
    )
    reasoning: str = Field(..., description="判定理由")
    needs_additional_round: bool = Field(
        ..., description="追加ラウンドが必要かどうか"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="判定時刻")


class IdentifiedIssue(BaseModel):
    """特定された課題"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="課題ID")
    title: str = Field(..., description="課題タイトル")
    description: str = Field(..., description="課題詳細")
    category: IssueCategory = Field(..., description="課題カテゴリ")
    priority: IssuePriority = Field(..., description="優先度")
    root_causes: List[str] = Field(
        default_factory=list, description="根本原因"
    )
    affected_areas: List[str] = Field(
        default_factory=list, description="影響範囲"
    )
    mentioned_by: List[str] = Field(
        default_factory=list, description="言及したペルソナ"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="作成時刻")


class ProposedSolution(BaseModel):
    """提案された解決策"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="解決策ID")
    issue_id: str = Field(..., description="対象課題ID")
    title: str = Field(..., description="解決策タイトル")
    description: str = Field(..., description="解決策詳細")
    implementation_steps: List[str] = Field(
        default_factory=list, description="実装ステップ"
    )
    required_resources: List[str] = Field(
        default_factory=list, description="必要リソース"
    )
    timeline: str = Field(..., description="実装期間")
    risks: List[str] = Field(default_factory=list, description="リスク")
    expected_outcomes: List[str] = Field(
        default_factory=list, description="期待効果"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="作成時刻")


class DiscussionSession(BaseModel):
    """議論セッション"""
    session_id: str = Field(
        default_factory=lambda: str(uuid4()), description="セッションID"
    )
    topic: str = Field(..., description="議論テーマ")
    organization_context: Dict[str, Any] = Field(
        default_factory=dict, description="組織コンテキスト"
    )
    status: DiscussionStatus = Field(
        default=DiscussionStatus.INITIALIZED, description="セッション状態"
    )
    rounds: List[DiscussionRound] = Field(
        default_factory=list, description="議論ラウンド一覧"
    )
    sufficiency_judgments: List[SufficiencyJudgment] = Field(
        default_factory=list, description="十分性判定一覧"
    )
    final_issues: List[IdentifiedIssue] = Field(
        default_factory=list, description="最終的に特定された課題"
    )
    final_solutions: List[ProposedSolution] = Field(
        default_factory=list, description="最終的に提案された解決策"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="作成時刻")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時刻")
    completed_at: Optional[datetime] = Field(default=None, description="完了時刻")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_round(self, participants: List[str]) -> DiscussionRound:
        """新しいラウンドを追加"""
        round_id = len(self.rounds) + 1
        new_round = DiscussionRound(round_id=round_id, participants=participants)
        self.rounds.append(new_round)
        self.updated_at = datetime.now()
        return new_round
    
    def add_sufficiency_judgment(self, judgment: SufficiencyJudgment) -> None:
        """十分性判定を追加"""
        self.sufficiency_judgments.append(judgment)
        self.updated_at = datetime.now()
    
    def complete_session(
        self,
        issues: List[IdentifiedIssue],
        solutions: List[ProposedSolution]
    ) -> None:
        """セッションを完了"""
        self.final_issues = issues
        self.final_solutions = solutions
        self.status = DiscussionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def get_current_round(self) -> Optional[DiscussionRound]:
        """現在のラウンドを取得"""
        if not self.rounds:
            return None
        return self.rounds[-1]
    
    def get_all_statements(self) -> List[PersonaStatement]:
        """全ての発言を取得"""
        statements = []
        for round_data in self.rounds:
            statements.extend(round_data.statements)
        return statements 