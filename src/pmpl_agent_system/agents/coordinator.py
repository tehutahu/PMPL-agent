"""メインコーディネーターエージェント"""

from typing import Dict, List, Optional
import asyncio

import structlog

from ..llm.manager import LLMInterface
from ..models.data import (
    DiscussionRound,
    DiscussionSession,
    DiscussionStatus,
    PersonaStatement,
)
from .personas import PersonaAgentFactory

logger = structlog.get_logger(__name__)


class MainCoordinator:
    """メインコーディネーターエージェント"""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.persona_factory = PersonaAgentFactory()
        self.system_prompt = """
あなたは複数のペルソナエージェントによる議論をファシリテートするメインコーディネーターです。

**責務**:
1. 議論テーマの論点を整理し、焦点を明確化する
2. ペルソナ間の対話を促進し、建設的な議論を誘導する
3. 意見の相違点を明確化し、深掘りすべき論点を特定する
4. 最終的な合意形成と統合された見解の作成を支援する

**議論進行の原則**:
- 全ペルソナが平等に発言機会を得られるようにする
- 意見の対立を恐れず、建設的な議論を促進する
- 具体的な事例や経験に基づく議論を重視する
- 人材マネジメントとプロセス改善の実践的解決策を目指す

対話的で深化した議論を通じて、10-50人規模IT組織の課題解決を目指してください。
"""
    
    async def start_discussion(
        self,
        session: DiscussionSession,
        llm_manager: 'LLMManager'  # type: ignore
    ) -> DiscussionRound:
        """対話的議論を開始"""
        # セッション状態を更新
        session.status = DiscussionStatus.ROUND1_IN_PROGRESS
        
        # 基本ペルソナでラウンドを作成
        basic_personas = self.persona_factory.get_basic_personas()
        discussion_round = session.add_round(basic_personas)
        
        # 対話的議論を実施
        await self._conduct_interactive_discussion(
            discussion_round,
            session.topic,
            session.organization_context,
            llm_manager
        )
        
        # ラウンド完了
        discussion_round.complete_round()
        session.status = DiscussionStatus.COMPLETED
        
        return discussion_round
    
    async def _conduct_interactive_discussion(
        self,
        discussion_round: DiscussionRound,
        topic: str,
        organization_context: Dict[str, any],  # type: ignore
        llm_manager: 'LLMManager'  # type: ignore
    ) -> None:
        """対話的議論の実施"""
        context = self._format_organization_context(organization_context)
        
        # Step 1: 論点整理と議題設定
        agenda = await self._set_discussion_agenda(topic, context)
        logger.info("議論の論点整理完了", agenda=agenda)
        
        # Step 2: 初期見解ラウンド
        await self._initial_statements_round(discussion_round, topic, context, llm_manager)
        
        # Step 3: 相互議論ラウンド（2-3回）
        for round_num in range(2, 4):
            logger.info(f"相互議論ラウンド{round_num}開始")
            await self._interactive_discussion_round(
                discussion_round, topic, context, llm_manager, round_num
            )
        
        # Step 4: 合意形成ラウンド  
        await self._consensus_building_round(discussion_round, topic, context, llm_manager)
        
        # Step 5: 議論総まとめ
        await self._generate_discussion_summary(discussion_round, topic, context)
    
    async def _set_discussion_agenda(self, topic: str, context: str) -> str:
        """議論の論点を整理し議題を設定"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""
議論テーマ: {topic}
コンテキスト: {context}

このテーマについて、以下の観点から主要な論点を3-5個整理してください：
1. 人材マネジメントの課題
2. プロセス改善の課題  
3. 組織スケーリングの課題

各論点について、議論すべき具体的なポイントを明示してください。
"""}
        ]
        
        agenda = await self.llm.generate(messages)
        return agenda
    
    async def _initial_statements_round(
        self,
        discussion_round: DiscussionRound,
        topic: str,
        context: str,
        llm_manager: 'LLMManager'  # type: ignore
    ) -> None:
        """初期見解表明ラウンド"""
        logger.info("初期見解表明ラウンド開始")
        
        for persona_name in discussion_round.participants:
            try:
                # ペルソナエージェントを作成
                persona_llm = llm_manager.get_llm(persona_name)
                persona_agent = self.persona_factory.create_agent(persona_name, persona_llm)
                
                # 初期見解を取得
                statement = await persona_agent.discuss(
                    topic,
                    context,
                    discussion_round.statements,
                    discussion_type="initial"
                )
                
                # 発言をラウンドに追加
                discussion_round.add_statement(statement)
                logger.info(f"{persona_name}の初期見解完了")
                
            except Exception as e:
                logger.error("ペルソナ初期見解エラー", persona=persona_name, error=str(e))
                continue
    
    async def _interactive_discussion_round(
        self,
        discussion_round: DiscussionRound,
        topic: str,
        context: str,
        llm_manager: 'LLMManager',  # type: ignore
        round_num: int
    ) -> None:
        """相互議論ラウンド"""
        # コーディネーターが焦点となる論点を特定
        focus_points = await self._identify_focus_points(discussion_round.statements, round_num)
        logger.info(f"ラウンド{round_num}の焦点論点", focus_points=focus_points)
        
        # 各ペルソナに他者の意見への応答を求める
        for persona_name in discussion_round.participants:
            try:
                persona_llm = llm_manager.get_llm(persona_name)
                persona_agent = self.persona_factory.create_agent(persona_name, persona_llm)
                
                # 他のペルソナの意見に対する応答を取得
                statement = await persona_agent.discuss(
                    topic,
                    context + f"\n\n焦点論点: {focus_points}",
                    discussion_round.statements,
                    discussion_type="interactive",
                    round_number=round_num
                )
                
                discussion_round.add_statement(statement)
                logger.info(f"{persona_name}のラウンド{round_num}応答完了")
                
            except Exception as e:
                logger.error("ペルソナ相互議論エラー", persona=persona_name, round=round_num, error=str(e))
                continue
    
    async def _identify_focus_points(self, statements: List[PersonaStatement], round_num: int) -> str:
        """議論の焦点となる論点を特定"""
        statements_summary = "\n\n".join([
            f"{stmt.persona_name}: {stmt.statement[:300]}..."
            for stmt in statements[-5:]  # 最新5件の発言
        ])
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""
これまでの議論:
{statements_summary}

ラウンド{round_num}で焦点を当てるべき論点を特定してください：
1. 意見が分かれている点
2. さらに深掘りが必要な課題
3. 具体的な解決策が求められている領域

次の議論で参加者が応答すべき具体的な問いかけを3つ提示してください。
"""}
        ]
        
        focus_points = await self.llm.generate(messages)
        return focus_points
    
    async def _consensus_building_round(
        self,
        discussion_round: DiscussionRound,
        topic: str,
        context: str,
        llm_manager: 'LLMManager'  # type: ignore
    ) -> None:
        """合意形成ラウンド"""
        logger.info("合意形成ラウンド開始")
        
        # これまでの議論を統合し、合意点を整理
        consensus_framework = await self._build_consensus_framework(discussion_round.statements)
        
        # 各ペルソナに最終的な統合見解を求める
        for persona_name in discussion_round.participants:
            try:
                persona_llm = llm_manager.get_llm(persona_name)
                persona_agent = self.persona_factory.create_agent(persona_name, persona_llm)
                
                statement = await persona_agent.discuss(
                    topic,
                    context + f"\n\n合意形成の枠組み: {consensus_framework}",
                    discussion_round.statements,
                    discussion_type="consensus"
                )
                
                discussion_round.add_statement(statement)
                logger.info(f"{persona_name}の合意形成完了")
                
            except Exception as e:
                logger.error("ペルソナ合意形成エラー", persona=persona_name, error=str(e))
                continue
    
    async def _build_consensus_framework(self, statements: List[PersonaStatement]) -> str:
        """合意形成の枠組みを構築"""
        all_statements = "\n\n".join([
            f"{stmt.persona_name}({stmt.persona_role}): {stmt.statement}"
            for stmt in statements
        ])
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""
これまでの全議論:
{all_statements}

以下の観点から合意形成の枠組みを整理してください：
1. 全員が同意している課題と解決策
2. 意見が分かれている点とその理由
3. 統合可能な解決策の方向性
4. 今後検討すべき残された論点

実践的で具体的な合意事項をまとめてください。
"""}
        ]
        
        framework = await self.llm.generate(messages)
        return framework

    def _format_organization_context(self, context: Dict[str, any]) -> str:  # type: ignore
        """組織コンテキストを文字列にフォーマット"""
        if not context:
            return ""
        
        formatted_parts = []
        
        if "company_size" in context:
            formatted_parts.append(f"組織規模: {context['company_size']}人")
        
        if "industry" in context:
            formatted_parts.append(f"業界: {context['industry']}")
        
        if "development_stage" in context:
            formatted_parts.append(f"発展段階: {context['development_stage']}")
        
        if "current_challenges" in context:
            challenges = context["current_challenges"]
            if isinstance(challenges, list):
                formatted_parts.append(f"現在の課題: {', '.join(challenges)}")
            else:
                formatted_parts.append(f"現在の課題: {challenges}")
        
        if "team_structure" in context:
            formatted_parts.append(f"チーム構成: {context['team_structure']}")
        
        return "\n".join(formatted_parts)

    async def _generate_discussion_summary(
        self,
        discussion_round: DiscussionRound,
        topic: str,
        context: str
    ) -> None:
        """議論の総まとめを生成"""
        logger.info("議論総まとめ開始")
        
        try:
            # 全ての発言を統合
            all_statements = "\n\n".join([
                f"【{stmt.persona_name}（{stmt.persona_role}）】\n{stmt.statement}"
                for stmt in discussion_round.statements
            ])
            
            # 特定された課題を統合
            all_issues = []
            for stmt in discussion_round.statements:
                all_issues.extend(stmt.identified_issues)
            
            # 提案された解決策を統合
            all_solutions = []
            for stmt in discussion_round.statements:
                all_solutions.extend(stmt.proposed_solutions)
            
            # コーディネーターによる総まとめを生成
            messages = [
                {"role": "system", "content": f"""
あなたは議論をファシリテートしたメインコーディネーターです。
これまでの議論を統合し、総まとめレポートを作成してください。

以下の構成でまとめてください：
1. 議論概要サマリー
2. 主要課題の整理（優先度付き）
3. 解決策の体系化
4. 実装ロードマップ
5. 今後の検討事項

具体的で実践的な内容を心がけ、PMPLが即座に活用できる形式で作成してください。
"""},
                {"role": "user", "content": f"""
議論テーマ: {topic}
組織コンテキスト: {context}

【全議論内容】
{all_statements}

【特定された課題一覧】（{len(all_issues)}件）
{chr(10).join([f"- {issue}" for issue in all_issues])}

【提案された解決策一覧】（{len(all_solutions)}件）
{chr(10).join([f"- {solution}" for solution in all_solutions])}

上記の議論を統合し、PMPLが活用できる総まとめレポートを作成してください。
"""}
            ]
            
            summary = await self.llm.generate(messages)
            
            # 総まとめをPersonaStatementとして記録
            from datetime import datetime
            summary_statement = PersonaStatement(
                persona_name="メインコーディネーター",
                persona_role="議論ファシリテーター",
                statement=summary,
                identified_issues=[],
                proposed_solutions=[],
                timestamp=datetime.now(),
                llm_model=self.llm.model_name
            )
            
            discussion_round.add_statement(summary_statement)
            logger.info("議論総まとめ完了")
            
        except Exception as e:
            logger.error("議論総まとめエラー", error=str(e))
            # エラーが発生しても議論は継続する 