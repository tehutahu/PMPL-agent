"""PMPLエージェントシステム メインクラス"""

from typing import Any, Dict, List, Optional, Set

from ..agents.coordinator import MainCoordinator
from ..config.settings import Settings, load_default_config
from ..llm.manager import LLMManager
from ..models.data import (
    DiscussionSession,
    DiscussionStatus,
    IdentifiedIssue,
    ProposedSolution,
)
from ..storage.local import LocalStorage


class PMPLAgentSystem:
    """PMPLエージェントシステム メインクラス"""
    
    def __init__(self, settings: Optional[Settings] = None):
        # 設定の初期化
        self.settings = settings or load_default_config()
        self.settings.validate_api_keys()
        
        # コンポーネントの初期化
        self.llm_manager = LLMManager(self.settings)
        self.storage = LocalStorage(self.settings.storage.path)
        self.coordinator = MainCoordinator(
            self.llm_manager.get_llm("coordinator")
        )
    
    async def start_discussion(
        self,
        topic: str,
        organization_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """新しい議論セッションを開始"""
        # セッションを作成
        session = DiscussionSession(
            topic=topic,
            organization_context=organization_context or {},
            status=DiscussionStatus.INITIALIZED
        )
        
        try:
            # セッションを保存
            await self.storage.save_session(session)
            
            # 第1ラウンド議論を開始
            round1 = await self.coordinator.start_discussion(
                session, self.llm_manager
            )
            
            # TODO: 課題十分性判定の実装
            # 現時点では基本ラウンドのみで完了とする
            
            # TODO: 課題分析・解決策生成の実装
            
            # セッションを完了状態に更新
            session.status = DiscussionStatus.COMPLETED
            await self.storage.save_session(session)
            
            return session.session_id
            
        except Exception as e:
            # エラー時はFAILED状態に設定
            session.status = DiscussionStatus.FAILED
            await self.storage.save_session(session)
            raise RuntimeError(f"議論セッション開始エラー: {e}")
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """セッションの状態を取得"""
        session = await self.storage.load_session(session_id)
        if not session:
            raise ValueError(f"セッションが見つかりません: {session_id}")
        
        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "rounds_count": len(session.rounds),
            "issues_count": len(session.final_issues),
            "solutions_count": len(session.final_solutions),
        }
    
    async def get_session_details(self, session_id: str) -> DiscussionSession:
        """セッションの詳細を取得"""
        session = await self.storage.load_session(session_id)
        if not session:
            raise ValueError(f"セッションが見つかりません: {session_id}")
        
        return session
    
    async def generate_report(self, session_id: str) -> str:
        """議論セッションのレポートを生成"""
        session = await self.storage.load_session(session_id)
        if not session:
            raise ValueError(f"セッションが見つかりません: {session_id}")
        
        if session.status != DiscussionStatus.COMPLETED:
            raise ValueError(f"セッションが完了していません: {session.status.value}")
        
        # TODO: ReportGeneratorの実装
        # 現時点では簡易的なレポートを返す
        return self._generate_simple_report(session)
    
    def _generate_simple_report(self, session: DiscussionSession) -> str:
        """簡易レポート生成"""
        report_lines = [
            f"# PMPL課題分析レポート",
            f"",
            f"**セッションID**: {session.session_id}",
            f"**議論テーマ**: {session.topic}",
            f"**作成日時**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
        ]
        
        # コーディネーターによる議論総まとめを最初に配置
        coordinator_summary = None
        for round_data in session.rounds:
            for statement in round_data.statements:
                if statement.persona_name == "メインコーディネーター":
                    coordinator_summary = statement.statement
                    break
            if coordinator_summary:
                break
        
        if coordinator_summary:
            report_lines.extend([
                f"## 🎯 エグゼクティブサマリー",
                f"",
                f"*メインコーディネーターによる議論総まとめ*",
                f"",
                coordinator_summary,
                f"",
                f"---",
                f"",
            ])
        
        report_lines.extend([
            f"## 議論参加者",
            f"",
        ])
        
        # 参加者紹介セクションを追加
        from ..agents.personas import PersonaAgentFactory
        persona_profiles = PersonaAgentFactory.create_persona_profiles()
        
        # 参加者を表形式で紹介
        report_lines.extend([
            f"| 役割 | 氏名 | 組織 | 経験年数 | 専門領域 |",
            f"|------|------|------|----------|----------|",
        ])
        
        participants: Set[str] = set()
        for round_data in session.rounds:
            participants.update(round_data.participants)
        
        # コーディネーターの情報を追加
        report_lines.append(f"| **コーディネーター** | システム | メインコーディネーター | - | 議論進行・合意形成支援 |")
        
        for participant in sorted(participants):
            if participant in persona_profiles:
                profile = persona_profiles[participant]
                specialties = "、".join(profile.specialties[:3])  # 最初の3つの専門領域のみ
                report_lines.append(
                    f"| {profile.role} | {profile.name} | {profile.company_type} | {profile.experience_years} | {specialties} |"
                )
        
        report_lines.extend([
            f"",
            f"---",
            f"",
            f"## 議論概要",
            f"",
        ])
        
        # 概要情報を表形式で整理
        total_statements = sum(len(r.statements) for r in session.rounds)
        total_issues = sum(len(stmt.identified_issues) for r in session.rounds for stmt in r.statements)
        total_solutions = sum(len(stmt.proposed_solutions) for r in session.rounds for stmt in r.statements)
        
        report_lines.extend([
            f"| 項目 | 値 |",
            f"|------|-----|",
            f"| ラウンド数 | {len(session.rounds)} |",
            f"| 総発言数 | {total_statements} |",
            f"| 参加者数 | {len(participants)} |",
            f"| 特定された課題数 | {total_issues} |",
            f"| 提案された解決策数 | {total_solutions} |",
            f"",
            f"---",
            f"",
        ])
        
        # 各ラウンドの詳細 - フェーズ別に整理
        for i, round_data in enumerate(session.rounds, 1):
            report_lines.extend([
                f"## ラウンド{i}の議論",
                f"",
                f"**期間**: {round_data.started_at.strftime('%Y-%m-%d %H:%M:%S')} ～ {round_data.completed_at.strftime('%Y-%m-%d %H:%M:%S') if round_data.completed_at else '未完了'}",
                f"",
                f"**参加者**: {', '.join(round_data.participants)}",
                f"",
            ])
            
            # 発言を議論フェーズごとに分類
            statements = round_data.statements
            if not statements:
                continue
                
            # フェーズごとに発言を分類 (5人 x 4フェーズ = 20発言の想定)
            participants_count = len(round_data.participants)
            phase_size = participants_count
            
            phases = [
                {"name": "フェーズ1: 初期見解表明", "description": "各専門家による課題の初期分析", "emoji": "🎯"},
                {"name": "フェーズ2: 相互議論 (前半)", "description": "他者の見解を踏まえた意見交換", "emoji": "💬"},
                {"name": "フェーズ3: 相互議論 (後半)", "description": "論点を深掘りした詳細議論", "emoji": "🔍"},
                {"name": "フェーズ4: 合意形成", "description": "統合的な見解と実行可能な解決策の提示", "emoji": "🤝"},
            ]
            
            for phase_idx, phase in enumerate(phases):
                start_idx = phase_idx * phase_size
                end_idx = min(start_idx + phase_size, len(statements))
                
                if start_idx >= len(statements):
                    break
                    
                phase_statements = statements[start_idx:end_idx]
                
                if not phase_statements:
                    continue
                
                report_lines.extend([
                    f"### {phase['emoji']} {phase['name']}",
                    f"",
                    f"*{phase['description']}*",
                    f"",
                ])
                
                # コーディネーターからの進行説明を追加
                if phase_idx == 0:
                    report_lines.extend([
                        f"#### 📋 コーディネーターより",
                        f"",
                        f"議論テーマ「{session.topic}」について、各専門家の視点から課題分析を開始します。",
                        f"人材マネジメント、プロセス改善、組織スケーリングの観点から、",
                        f"10-50人規模IT組織特有の課題を特定し、実践的な解決策を検討してください。",
                        f"",
                        f"---",
                        f"",
                    ])
                elif phase_idx == 1:
                    report_lines.extend([
                        f"#### 📋 コーディネーターより",
                        f"",
                        f"初期見解を踏まえ、以下の論点について相互議論を進めます：",
                        f"- 意見が分かれている課題の詳細分析",
                        f"- より具体的な解決策の検討",
                        f"- 実装時の課題と対策の議論",
                        f"",
                        f"---",
                        f"",
                    ])
                elif phase_idx == 2:
                    report_lines.extend([
                        f"#### 📋 コーディネーターより",
                        f"",
                        f"これまでの議論を深掘りし、以下に焦点を当てて検討してください：",
                        f"- 根本原因の特定と分析",
                        f"- 段階的な実装アプローチ",
                        f"- 組織の成熟度に応じた対策",
                        f"",
                        f"---",
                        f"",
                    ])
                elif phase_idx == 3:
                    report_lines.extend([
                        f"#### 📋 コーディネーターより",
                        f"",
                        f"最終フェーズとして、統合的な見解をまとめてください：",
                        f"- 優先度の高い課題の絞り込み",
                        f"- 実現可能性の高い解決策の提案",
                        f"- 具体的な実行計画とタイムライン",
                        f"",
                        f"---",
                        f"",
                    ])
                
                # 各発言の表示
                for j, statement in enumerate(phase_statements, 1):
                    global_index = start_idx + j
                    report_lines.extend([
                        f"#### {global_index}. {statement.persona_name}（{statement.persona_role}）",
                        f"",
                        f"{statement.statement}",
                        f"",
                    ])
                    
                    # 課題と解決策の詳細表示は各フェーズの最初と最後のみ
                    if j == 1 or j == len(phase_statements):
                        report_lines.extend([
                            f"##### 特定した課題と提案した解決策",
                            f"",
                        ])
                        
                        if statement.identified_issues:
                            report_lines.extend([
                                f"**特定した課題** ({len(statement.identified_issues)}件):",
                            ])
                            for k, issue in enumerate(statement.identified_issues, 1):
                                report_lines.append(f"  {k}. {issue}")
                            report_lines.append("")
                        
                        if statement.proposed_solutions:
                            report_lines.extend([
                                f"**提案した解決策** ({len(statement.proposed_solutions)}件):",
                            ])
                            for k, solution in enumerate(statement.proposed_solutions, 1):
                                report_lines.append(f"  {k}. {solution}")
                            report_lines.append("")
                    else:
                        # その他の発言では簡潔な要約のみ
                        issue_count = len(statement.identified_issues)
                        solution_count = len(statement.proposed_solutions)
                        report_lines.extend([
                            f"*課題 {issue_count}件、解決策 {solution_count}件を提示*",
                            f"",
                        ])
                    
                    report_lines.extend([
                        f"---",
                        f"",
                    ])
                
                # フェーズ間の区切り
                if phase_idx < len(phases) - 1 and end_idx < len(statements):
                    report_lines.extend([
                        f"",
                        f"🔄 **フェーズ移行**",
                        f"",
                    ])
        
        # 最終的な課題と解決策のサマリー
        if session.final_issues or session.final_solutions:
            report_lines.extend([
                f"## 📊 議論のまとめ",
                f"",
            ])
            
            if session.final_issues:
                report_lines.extend([
                    f"### 🎯 合意された主要課題",
                    f"",
                ])
                for i, issue in enumerate(session.final_issues, 1):
                    report_lines.append(f"{i}. **{issue.title}** - {issue.description}")
                report_lines.append("")
            
            if session.final_solutions:
                report_lines.extend([
                    f"### 💡 提案された解決策",
                    f"",
                ])
                for i, solution in enumerate(session.final_solutions, 1):
                    report_lines.append(f"{i}. **{solution.title}** - {solution.description}")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """セッション一覧を取得"""
        sessions = await self.storage.list_sessions()
        return [
            {
                "session_id": session.session_id,
                "topic": session.topic,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "rounds_count": len(session.rounds),
            }
            for session in sessions
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        try:
            # LLMプロバイダーのヘルスチェック
            llm_health = await self.llm_manager.health_check()
            
            # ストレージのヘルスチェック
            storage_health = await self.storage.health_check()
            
            return {
                "status": "healthy",
                "llm_providers": llm_health,
                "storage": storage_health,
                "settings": {
                    "default_provider": self.settings.default_llm.provider,
                    "default_model": self.settings.default_llm.model,
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            } 