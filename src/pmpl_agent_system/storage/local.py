"""ローカルファイルストレージ実装"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict

import aiofiles

from ..models.data import DiscussionSession


class LocalStorage:
    """ローカルファイルストレージ"""
    
    def __init__(self, storage_path: str = "./data/discussions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def save_session(self, session: DiscussionSession) -> None:
        """セッションを保存"""
        session_file = self.storage_path / f"{session.session_id}.json"
        
        # Pydanticモデルをdict形式でJSONシリアライズ
        session_data = session.model_dump(mode="json")
        
        async with aiofiles.open(session_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(session_data, ensure_ascii=False, indent=2))
    
    async def load_session(self, session_id: str) -> Optional[DiscussionSession]:
        """セッションを読み込み"""
        session_file = self.storage_path / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        try:
            async with aiofiles.open(session_file, "r", encoding="utf-8") as f:
                session_data = json.loads(await f.read())
            
            return DiscussionSession.model_validate(session_data)
        except Exception:
            return None
    
    async def list_sessions(self) -> List[DiscussionSession]:
        """すべてのセッションを一覧取得"""
        sessions = []
        
        for session_file in self.storage_path.glob("*.json"):
            try:
                async with aiofiles.open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.loads(await f.read())
                
                session = DiscussionSession.model_validate(session_data)
                sessions.append(session)
            except Exception:
                # 破損したファイルはスキップ
                continue
        
        return sorted(sessions, key=lambda x: x.created_at, reverse=True)
    
    async def delete_session(self, session_id: str) -> bool:
        """セッションを削除"""
        session_file = self.storage_path / f"{session_id}.json"
        
        if session_file.exists():
            try:
                os.remove(session_file)
                return True
            except Exception:
                return False
        
        return False
    
    async def health_check(self) -> Dict[str, any]:  # type: ignore
        """ストレージヘルスチェック"""
        try:
            # ディレクトリの存在確認
            if not self.storage_path.exists():
                return {
                    "status": "unhealthy",
                    "error": "ストレージディレクトリが存在しません"
                }
            
            # 書き込み権限確認
            test_file = self.storage_path / ".health_check"
            test_file.write_text("test")
            test_file.unlink()
            
            # ファイル数カウント
            file_count = len(list(self.storage_path.glob("*.json")))
            
            return {
                "status": "healthy",
                "storage_path": str(self.storage_path),
                "file_count": file_count,
                "writable": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            } 