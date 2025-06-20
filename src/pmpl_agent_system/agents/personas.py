"""ペルソナエージェントシステム"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
import yaml

from ..llm.manager import LLMInterface
from ..models.data import PersonaStatement

logger = structlog.get_logger(__name__)

# デフォルトのペルソナ設定ファイルパス
# リポジトリルートの `config/personas.yaml` を参照する
DEFAULT_PERSONA_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "personas.yaml"
)


@dataclass
class PersonaConfig:
    """ペルソナ設定"""
    name: str
    role: str
    experience_years: int
    organization_type: str
    expertise_areas: list[str]
    system_prompt: str
    llm_config: str


@dataclass
class PersonaProfile:
    """ペルソナプロファイル"""
    name: str
    role: str
    company_type: str
    experience_years: str
    specialties: list[str]
    perspective: str
    communication_style: str


class PersonaAgent:
    """ペルソナエージェントの基底クラス"""

    def __init__(self, llm: LLMInterface, profile: PersonaProfile):
        self.llm = llm
        self.profile = profile

    async def discuss(
        self,
        topic: str,
        context: str,
        previous_statements: list[PersonaStatement],
        discussion_type: str = "initial",
        round_number: int = 1
    ) -> PersonaStatement:
        """議論に参加して発言を生成
        Args:
            topic: 議論テーマ
            context: 組織コンテキスト
            previous_statements: これまでの発言
            discussion_type: 議論タイプ（initial/interactive/consensus）
            round_number: ラウンド数
        """

        # 議論タイプに応じたプロンプトを生成
        system_prompt = self._generate_system_prompt(discussion_type)
        user_prompt = self._generate_user_prompt(
            topic, context, previous_statements, discussion_type, round_number
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # LLMから発言を生成
        response = await self.llm.generate(messages)

        # 課題と解決策を抽出
        issues, solutions = await self._extract_issues_and_solutions(response)

        # PersonaStatementを作成
        statement = PersonaStatement(
            persona_name=self.profile.name,
            persona_role=self.profile.role,
            statement=response,
            identified_issues=issues,
            proposed_solutions=solutions,
            llm_model=self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown"
        )

        logger.info(
            "ペルソナ発言生成完了",
            persona=self.profile.name,
            discussion_type=discussion_type,
            round=round_number,
            issues_count=len(issues),
            solutions_count=len(solutions)
        )

        return statement

    def _generate_system_prompt(self, discussion_type: str) -> str:
        """議論タイプに応じたシステムプロンプトを生成"""
        base_prompt = f"""
あなたは{self.profile.name}（{self.profile.role}）として行動してください。

**あなたのプロファイル:**
- 所属: {self.profile.company_type}
- 経験: {self.profile.experience_years}
- 専門分野: {', '.join(self.profile.specialties)}
- 視点: {self.profile.perspective}
- コミュニケーションスタイル: {self.profile.communication_style}

**基本姿勢:**
- 10-50人規模のIT組織における実践的な知見を提供する
- 具体的な経験や事例に基づいて発言する
- 他の参加者の意見を尊重しつつ、建設的な議論を行う
- 人材マネジメントとプロセス改善の実用的解決策を重視する
"""

        if discussion_type == "initial":
            return base_prompt + """
**このラウンドでの役割:**
議論テーマについて、あなたの専門性と経験に基づく初期見解を表明してください。
- 重要と考える課題を3-5個特定する
- 各課題に対する実践的な解決策を提案する
- 具体的な事例や経験を交えて説明する
"""

        elif discussion_type == "interactive":
            return base_prompt + """
**このラウンドでの役割:**
他の参加者の意見を踏まえ、対話的な議論を行ってください。
- 他者の意見に対する同意点・相違点を明確化する
- 新たな視点や見落とされた課題があれば指摘する
- 実践的な改善案や代替案を提案する
- 建設的な議論を通じて課題理解を深化させる
"""

        elif discussion_type == "consensus":
            return base_prompt + """
**このラウンドでの役割:**
これまでの議論を統合し、合意形成に向けた最終見解を提示してください。
- 議論で合意された重要な課題をまとめる
- 実現可能性の高い解決策を優先順位付けする
- 組織の段階的な改善計画を提案する
- 今後の課題として残る論点を整理する
"""

        return base_prompt

    def _generate_user_prompt(
        self,
        topic: str,
        context: str,
        previous_statements: list[PersonaStatement],
        discussion_type: str,
        round_number: int
    ) -> str:
        """ユーザープロンプトを生成"""
        prompt = f"""
**議論テーマ:** {topic}

**組織コンテキスト:**
{context}
"""

        if previous_statements:
            if discussion_type == "initial":
                # 初期ラウンドでは他者の発言は参考程度
                if len(previous_statements) > 0:
                    recent_statements = previous_statements[-2:]  # 最新2件
                    prompt += "\n**これまでの発言（参考）:**\n"
                    for stmt in recent_statements:
                        prompt += f"- {stmt.persona_name}: {stmt.statement[:200]}...\n"

            elif discussion_type == "interactive":
                # 相互議論では他者の意見に対する応答を重視
                prompt += "\n**これまでの議論:**\n"
                for stmt in previous_statements[-5:]:  # 最新5件
                    prompt += f"\n**{stmt.persona_name}（{stmt.persona_role}）の見解:**\n"
                    prompt += f"{stmt.statement}\n"

                prompt += f"\n**ラウンド{round_number}での議論指針:**\n"
                prompt += "上記の意見を踏まえ、以下の観点で応答してください：\n"
                prompt += "1. 他者の意見で共感する点・疑問に思う点\n"
                prompt += "2. あなたの経験から見た追加の課題や視点\n"
                prompt += "3. より実現可能性の高い解決策の提案\n"
                prompt += "4. 具体的な実装方法や注意点\n"

            elif discussion_type == "consensus":
                # 合意形成では全体的な統合を重視
                prompt += "\n**全議論の要約:**\n"
                all_issues = []
                all_solutions = []
                for stmt in previous_statements:
                    all_issues.extend(stmt.identified_issues)
                    all_solutions.extend(stmt.proposed_solutions)

                prompt += f"特定された課題: {len(all_issues)}件\n"
                prompt += f"提案された解決策: {len(all_solutions)}件\n"

                prompt += "\n**合意形成の観点:**\n"
                prompt += "1. 最も重要で合意可能な課題を3つ選定する\n"
                prompt += "2. 実現可能性が高い解決策を優先順位付けする\n"
                prompt += "3. 段階的な実装計画を提案する\n"
                prompt += "4. 効果測定の指標を提案する\n"

        if discussion_type == "initial":
            prompt += "\n**回答形式:**\n"
            prompt += "あなたの専門性に基づく見解を詳細に述べてください。具体的な事例や経験談を含めて説明し、実践的な課題と解決策を提示してください。"

        elif discussion_type == "interactive":
            prompt += "\n**回答形式:**\n"
            prompt += "他者の意見を引用しながら、対話的な形式で応答してください。合意点と相違点を明確にし、建設的な議論を促進する内容としてください。"

        elif discussion_type == "consensus":
            prompt += "\n**回答形式:**\n"
            prompt += "これまでの議論を統合した最終見解を提示してください。合意事項、実行計画、今後の課題を明確に整理してください。"

        return prompt

    async def _extract_issues_and_solutions(self, statement: str) -> tuple[list[str], list[str]]:
        """発言から課題と解決策を抽出"""
        extraction_prompt = f"""
以下の発言から、具体的な課題と解決策を抽出してください：

発言内容：
{statement}

以下の形式で出力してください：

課題：
1. [課題1]
2. [課題2]
...

解決策：
1. [解決策1]
2. [解決策2]
...
"""

        try:
            messages = [
                {"role": "user", "content": extraction_prompt}
            ]
            extraction_result = await self.llm.generate(messages)

            # 課題と解決策を抽出
            issues = []
            solutions = []

            lines = extraction_result.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if '課題：' in line or '課題:' in line:
                    current_section = 'issues'
                elif '解決策：' in line or '解決策:' in line:
                    current_section = 'solutions'
                elif line and (line.startswith('1.') or line.startswith('2.') or
                              line.startswith('3.') or line.startswith('4.') or
                              line.startswith('5.')):
                    content = line[2:].strip()
                    if current_section == 'issues':
                        issues.append(content)
                    elif current_section == 'solutions':
                        solutions.append(content)

            logger.info(
                "課題・解決策抽出完了",
                persona=self.profile.name,
                issues_count=len(issues),
                solutions_count=len(solutions)
            )

            return issues, solutions

        except Exception as e:
            logger.error(
                "課題・解決策抽出エラー",
                persona=self.profile.name,
                error=str(e)
            )
            return [], []


class BasePersonaAgent:
    """基本ペルソナエージェント"""

    def __init__(self, config: PersonaConfig, llm: LLMInterface):
        self.config = config
        self.llm = llm

    async def discuss(
        self,
        topic: str,
        context: str = "",
        previous_statements: list[PersonaStatement] | None = None
    ) -> PersonaStatement:
        """議論に参加して見解を述べる"""
        try:
            # 会話履歴を構築
            messages = self._build_conversation_context(
                topic, context, previous_statements or []
            )

            # LLMで応答を生成
            response = await self.llm.generate(messages)

            # レスポンスから課題と解決策を抽出
            issues, solutions = self._extract_issues_and_solutions(response)

            # PersonaStatementを作成
            statement = PersonaStatement(
                persona_name=self.config.name,
                persona_role=self.config.role,
                statement=response,
                identified_issues=issues,
                proposed_solutions=solutions,
                llm_model=self.llm.model_name
            )

            logger.info(
                "ペルソナ発言生成完了",
                persona=self.config.name,
                issues_count=len(issues),
                solutions_count=len(solutions)
            )

            return statement

        except Exception as e:
            logger.error(
                "ペルソナ発言生成エラー",
                persona=self.config.name,
                error=str(e)
            )
            raise

    def _build_conversation_context(
        self,
        topic: str,
        context: str,
        previous_statements: list[PersonaStatement]
    ) -> list[dict[str, str]]:
        """会話コンテキストを構築"""
        messages = [
            {"role": "system", "content": self.config.system_prompt}
        ]

        # トピックとコンテキストを追加
        user_content = f"議論テーマ: {topic}\n\n"
        if context:
            user_content += f"コンテキスト: {context}\n\n"

        # 他のペルソナの発言があれば追加
        if previous_statements:
            user_content += "これまでの議論:\n"
            for stmt in previous_statements:
                user_content += f"\n{stmt.persona_name}({stmt.persona_role})の見解:\n"
                user_content += f"{stmt.statement}\n"
                if stmt.identified_issues:
                    user_content += f"特定した課題: {', '.join(stmt.identified_issues)}\n"
            user_content += "\n"

        user_content += (
            "上記を踏まえて、あなたの専門領域と経験から見た課題と解決策を述べてください。\n"
            "特に人材マネジメントとプロセス改善の観点から、具体的で実践的な見解をお願いします。"
        )

        messages.append({"role": "user", "content": user_content})

        return messages

    def _extract_issues_and_solutions(self, response: str) -> tuple[list[str], list[str]]:
        """レスポンスから課題と解決策を抽出"""
        # 簡易的なキーワードベース抽出
        # 実際の実装ではより高度なNLP処理を行う可能性がある

        issues = []
        solutions = []

        # 課題を示すキーワード
        issue_keywords = [
            "課題", "問題", "困っている", "難しい", "悩み", "リスク",
            "不足", "欠如", "足りない", "改善が必要", "ボトルネック"
        ]

        # 解決策を示すキーワード
        solution_keywords = [
            "解決策", "対策", "改善案", "提案", "施策", "アプローチ",
            "実施すべき", "導入", "取り組み", "方法", "戦略"
        ]

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 課題の抽出
            for keyword in issue_keywords:
                if keyword in line and len(line) > 10:
                    issues.append(line)
                    break

            # 解決策の抽出
            for keyword in solution_keywords:
                if keyword in line and len(line) > 10:
                    solutions.append(line)
                    break

        return issues[:5], solutions[:5]  # 最大5個まで


class ITStartupPMAgent(BasePersonaAgent):
    """ITスタートアップPMペルソナ"""
    pass


class EnterprisePMAgent(BasePersonaAgent):
    """エンタープライズPMペルソナ"""
    pass


class TechLeadAgent(BasePersonaAgent):
    """テックリードペルソナ"""
    pass


class ScrumMasterAgent(BasePersonaAgent):
    """スクラムマスターペルソナ"""
    pass


class EngineeringManagerAgent(BasePersonaAgent):
    """エンジニアリングマネージャーペルソナ"""
    pass


class HRSpecializedPMAgent(BasePersonaAgent):
    """HR特化PMペルソナ"""
    pass


class ProductOwnerAgent(BasePersonaAgent):
    """プロダクトオーナーペルソナ"""
    pass


class SeniorConsultantAgent(BasePersonaAgent):
    """シニアコンサルタントペルソナ"""
    pass


class PersonaAgentFactory:
    """ペルソナエージェントファクトリー"""

    @staticmethod
    def get_basic_personas() -> list[str]:
        """基本ペルソナ一覧を取得"""
        return [
            "startup_pm",
            "enterprise_pm",
            "tech_lead",
            "scrum_master",
            "engineering_manager"
        ]

    @staticmethod
    def get_supplementary_personas() -> list[str]:
        """補完ペルソナ一覧を取得"""
        return [
            "hr_specialized_pm",
            "product_owner",
            "senior_consultant"
        ]

    @staticmethod
    def create_persona_configs(path: Path | None = None) -> dict[str, PersonaConfig]:
        """ペルソナ設定を作成

        Parameters
        ----------
        path : Path | None, optional
            読み込む設定ファイルパス。未指定時は ``DEFAULT_PERSONA_PATH`` を利用する。
        """
        yaml_path = path or DEFAULT_PERSONA_PATH
        if not yaml_path.exists():
            raise FileNotFoundError(
                f"ペルソナ設定ファイルが見つかりません: {yaml_path}"
            )

        with open(yaml_path, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        configs = {}
        for name, persona in data.get("personas", {}).items():
            config_data = persona.get("config")
            if config_data:
                configs[name] = PersonaConfig(**config_data)

        return configs

    @staticmethod
    def create_agent(
        persona_name: str,
        llm: LLMInterface
    ) -> PersonaAgent:
        """ペルソナエージェントを作成"""
        profiles = PersonaAgentFactory.create_persona_profiles()

        if persona_name not in profiles:
            raise ValueError(f"Unknown persona: {persona_name}")

        profile = profiles[persona_name]
        return PersonaAgent(llm, profile)

    @staticmethod
    def create_persona_profiles(path: Path | None = None) -> dict[str, PersonaProfile]:
        """ペルソナプロファイルを作成

        Parameters
        ----------
        path : Path | None, optional
            読み込む設定ファイルパス。未指定時は ``DEFAULT_PERSONA_PATH`` を利用する。
        """
        yaml_path = path or DEFAULT_PERSONA_PATH
        if not yaml_path.exists():
            raise FileNotFoundError(
                f"ペルソナ設定ファイルが見つかりません: {yaml_path}"
            )

        with open(yaml_path, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        profiles = {}
        for name, persona in data.get("personas", {}).items():
            profile_data = persona.get("profile")
            if profile_data:
                profiles[name] = PersonaProfile(**profile_data)

        return profiles
