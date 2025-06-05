#!/usr/bin/env python3
"""簡単な動作テスト"""

import asyncio
import os
from src.pmpl_agent_system.core.system import PMPLAgentSystem

async def test_discussion():
    """議論のテスト"""
    # 環境変数でAPIキーが設定されていることを確認
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY環境変数が設定されていません")
        return
        
    try:
        system = PMPLAgentSystem()
        print("✅ システム初期化完了")
        
        # 議論開始
        session_id = await system.start_discussion("テスト議論")
        print(f"✅ 議論開始完了: {session_id}")
        
        # セッション状態確認
        status = await system.get_session_status(session_id)
        print(f"✅ セッション状態: {status}")
        
        # レポート生成
        report = await system.generate_report(session_id)
        print(f"✅ レポート生成完了")
        print("=" * 50)
        print(report[:500])
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_discussion()) 