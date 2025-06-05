"""コマンドラインインターフェース"""

import asyncio
import sys
from typing import Optional
import os

import click

from .core.system import PMPLAgentSystem


@click.group()
@click.version_option()
def cli() -> None:
    """PMPL エージェントシステム - プロダクトマネージャー・リーダーの課題議論・分析システム"""
    pass


@cli.command()
@click.argument("topic")
@click.option("--company-size", type=int, help="組織規模（人数）")
@click.option("--industry", help="業界")
@click.option("--stage", help="発展段階")
@click.option("--challenges", help="現在の課題（カンマ区切り）")
@click.option("--config", help="設定ファイルパス")
def start(
    topic: str,
    company_size: Optional[int] = None,
    industry: Optional[str] = None,
    stage: Optional[str] = None,
    challenges: Optional[str] = None,
    config: Optional[str] = None,
) -> None:
    """新しい議論セッションを開始"""
    
    async def _start_discussion() -> None:
        try:
            # 組織コンテキストを構築
            organization_context = {}
            if company_size:
                organization_context["company_size"] = company_size
            if industry:
                organization_context["industry"] = industry
            if stage:
                organization_context["development_stage"] = stage
            if challenges:
                organization_context["current_challenges"] = [
                    c.strip() for c in challenges.split(",")
                ]
            
            # システムを初期化
            system = PMPLAgentSystem()
            
            click.echo(f"議論セッションを開始します...")
            click.echo(f"テーマ: {topic}")
            if organization_context:
                click.echo(f"コンテキスト: {organization_context}")
            
            # 議論を開始
            session_id = await system.start_discussion(topic, organization_context)
            
            click.echo(f"✅ 議論セッション完了")
            click.echo(f"セッションID: {session_id}")
            
            # レポートを生成
            report = await system.generate_report(session_id)
            
            # reportsディレクトリを作成（存在しない場合）
            os.makedirs("reports", exist_ok=True)
            
            # レポートをファイルに保存
            report_file = f"reports/report_{session_id}.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)
            
            click.echo(f"📄 レポートを生成しました: {report_file}")
            
        except Exception as e:
            click.echo(f"❌ エラーが発生しました: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_start_discussion())


@cli.command()
@click.argument("session_id")
def status(session_id: str) -> None:
    """セッションの状態を確認"""
    
    async def _get_status() -> None:
        try:
            system = PMPLAgentSystem()
            session_status = await system.get_session_status(session_id)
            
            click.echo(f"セッション状態:")
            click.echo(f"  ID: {session_status['session_id']}")
            click.echo(f"  テーマ: {session_status['topic']}")
            click.echo(f"  状態: {session_status['status']}")
            click.echo(f"  作成日時: {session_status['created_at']}")
            click.echo(f"  更新日時: {session_status['updated_at']}")
            if session_status['completed_at']:
                click.echo(f"  完了日時: {session_status['completed_at']}")
            click.echo(f"  ラウンド数: {session_status['rounds_count']}")
            click.echo(f"  課題数: {session_status['issues_count']}")
            click.echo(f"  解決策数: {session_status['solutions_count']}")
            
        except Exception as e:
            click.echo(f"❌ エラーが発生しました: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_get_status())


@cli.command()
@click.argument("session_id")
@click.option("--output", "-o", help="出力ファイル名")
def report(session_id: str, output: Optional[str] = None) -> None:
    """レポートを生成"""
    
    async def _generate_report() -> None:
        try:
            system = PMPLAgentSystem()
            report_content = await system.generate_report(session_id)
            
            # reportsディレクトリを作成（存在しない場合）
            os.makedirs("reports", exist_ok=True)
            
            # 出力先を決定
            if output:
                output_file = output
            else:
                output_file = f"reports/report_{session_id}.md"
            
            # ファイルに保存
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            click.echo(f"📄 レポートを生成しました: {output_file}")
            
        except Exception as e:
            click.echo(f"❌ エラーが発生しました: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_generate_report())


@cli.command()
def list() -> None:
    """セッション一覧を表示"""
    
    async def _list_sessions() -> None:
        try:
            system = PMPLAgentSystem()
            sessions = await system.list_sessions()
            
            if not sessions:
                click.echo("セッションがありません")
                return
            
            click.echo(f"セッション一覧 ({len(sessions)}件):")
            click.echo("")
            
            for session in sessions:
                click.echo(f"📋 {session['session_id']}")
                click.echo(f"   テーマ: {session['topic']}")
                click.echo(f"   状態: {session['status']}")
                click.echo(f"   作成日時: {session['created_at']}")
                click.echo(f"   ラウンド数: {session['rounds_count']}")
                click.echo("")
                
        except Exception as e:
            click.echo(f"❌ エラーが発生しました: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_list_sessions())


@cli.command()
def health() -> None:
    """システムヘルスチェック"""
    
    async def _health_check() -> None:
        try:
            system = PMPLAgentSystem()
            health_result = await system.health_check()
            
            click.echo(f"システム状態: {health_result['status']}")
            
            if health_result['status'] == 'healthy':
                click.echo("✅ システムは正常です")
                
                # LLMプロバイダー状態
                click.echo("\nLLMプロバイダー状態:")
                for provider, status in health_result['llm_providers'].items():
                    status_icon = "✅" if status else "❌"
                    click.echo(f"  {status_icon} {provider}")
                
                # ストレージ状態
                storage = health_result['storage']
                storage_icon = "✅" if storage['status'] == 'healthy' else "❌"
                click.echo(f"\nストレージ状態:")
                click.echo(f"  {storage_icon} ステータス: {storage['status']}")
                if 'file_count' in storage:
                    click.echo(f"  📁 ファイル数: {storage['file_count']}")
                
                # 設定情報
                settings = health_result['settings']
                click.echo(f"\n設定情報:")
                click.echo(f"  🤖 デフォルトプロバイダー: {settings['default_provider']}")
                click.echo(f"  🧠 デフォルトモデル: {settings['default_model']}")
                
            else:
                click.echo("❌ システムに問題があります")
                if 'error' in health_result:
                    click.echo(f"エラー: {health_result['error']}")
                
        except Exception as e:
            click.echo(f"❌ エラーが発生しました: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_health_check())


def main() -> None:
    """メインエントリーポイント"""
    cli()


if __name__ == "__main__":
    main() 