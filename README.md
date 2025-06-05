# PMPL エージェントシステム

プロダクトマネージャー・プロダクトリーダー（PMPL）の人材マネジメント・プロセス改善課題を、複数ペルソナエージェントの議論により洗い出し、解決策を提案するシステムです。

## 特徴

- **多様なペルソナ**: ITスタートアップPM、エンタープライズPM、テックリード、スクラムマスター、エンジニアリングマネージャーなど
- **対話的議論フロー**: 5フェーズの構造化された議論進行（初期見解→相互議論→合意形成→総まとめ）
- **コーディネーター総まとめ**: 議論終了時の統合レポートとエグゼクティブサマリー自動生成
- **構造化レポート**: Markdown形式での詳細分析レポート生成（`reports/`ディレクトリに出力）
- **柔軟なLLM管理**: OpenAI/Anthropic等の複数プロバイダー対応

## 対象ユーザー

- **IT業界の10-50人規模組織**におけるPMPL
- **組織改善を支援するコンサルタント**
- **チーム・組織運営に課題を持つリーダー**

## 技術スタック

- **Python 3.11+** - メイン言語
- **Strands Agents SDK** - エージェントフレームワーク
- **OpenAI/Anthropic API** - LLMプロバイダー
- **Pydantic** - データ検証・シリアライゼーション
- **FastAPI** - API基盤（将来実装）
- **uv** - パッケージ管理

## インストール

### Docker環境（推奨）

```bash
# プロジェクトをクローン
git clone <repository-url>
cd pmpl-agent-system

# Docker環境をセットアップ
make setup

# コンテナに入る
make shell

# コンテナ内でアプリケーションを実行
pmpl-agent --help
```

### ローカル環境

```bash
# uvをインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトをクローン
git clone <repository-url>
cd pmpl-agent-system

# 依存関係をインストール
uv sync
```

### 環境設定

プロジェクトを動作させるには、API キーなどの環境変数を設定する必要があります。`env-sample.txt`ファイルをテンプレートとして`.env`ファイルを作成してください。

#### .envファイルの作成手順

1. **テンプレートファイルをコピー**
   ```bash
   cp env-sample.txt .env
   ```

2. **APIキーを設定**
   `.env`ファイルを編集して、以下の値を設定してください：

   ```bash
   # OpenAI API設定（必須）
   OPENAI_API_KEY=sk-your_actual_openai_api_key_here

   # オプション: Anthropic API設定（使用する場合）
   # ANTHROPIC_API_KEY=your_anthropic_api_key_here

   # ログレベル設定（デフォルト: INFO）
   LOG_LEVEL=INFO
   ```

3. **APIキーの取得方法**
   - **OpenAI API Key**: [OpenAI API platform](https://platform.openai.com/api-keys)でアカウント作成後、APIキーを生成
   - **Anthropic API Key**（オプション）: [Anthropic Console](https://console.anthropic.com/)でアカウント作成後、APIキーを生成

4. **注意事項**
   - `.env`ファイルは機密情報を含むため、Gitにコミットしないよう注意してください（`.gitignore`に既に追加済み）
   - OpenAI APIキーは`sk-`で始まる形式です
   - ログレベルは`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`から選択可能です

#### Docker環境とローカル環境の共通設定

上記の手順で作成した`.env`ファイルは、Docker環境・ローカル環境の両方で自動的に読み込まれます。

### 設定ファイルの確認

`config/default.yaml`で各種設定を調整できます：

- LLMプロバイダー・モデルの選択
- エージェント別設定
- 議論パラメーター
- ストレージ設定

## Docker環境での利用

### 基本的なコマンド

```bash
# 環境を起動
make up

# コンテナに入る
make shell

# ログを確認
make logs

# 環境を停止
make down

# テストを実行
make test

# リンターを実行
make lint

# コードフォーマット
make format
```

### VSCode Dev Container

このプロジェクトはVSCode Dev Containerに対応しています：

1. VSCodeで「Dev Containers」拡張機能をインストール
2. プロジェクトフォルダを開く
3. 「Reopen in Container」を選択
4. 自動的にDocker環境がセットアップされます

## 使用方法

### CLI経由での利用

#### 新しい議論セッションの開始

**Docker環境の場合**:
```bash
# コンテナに入る
make shell

# 基本的な使用方法
pmpl-agent start "スタートアップでのエンジニア採用とオンボーディング課題"

# 組織コンテキストを指定
pmpl-agent start "開発プロセス改善" \
  --company-size 25 \
  --industry "SaaS" \
  --stage "成長期" \
  --challenges "技術的負債,リリース品質,チーム間連携"
```

**ローカル環境の場合**:
```bash
# 基本的な使用方法
pmpl-agent start "スタートアップでのエンジニア採用とオンボーディング課題"

# 組織コンテキストを指定
pmpl-agent start "開発プロセス改善" \
  --company-size 25 \
  --industry "SaaS" \
  --stage "成長期" \
  --challenges "技術的負債,リリース品質,チーム間連携"
```

#### セッション管理

```bash
# セッション一覧表示
pmpl-agent list

# セッション状態確認
pmpl-agent status <session-id>

# レポート生成
pmpl-agent report <session-id> -o custom_report.md

# レポートはデフォルトで reports/ ディレクトリに出力されます
# カスタムパスを指定しない場合: reports/report_<session-id>.md
```

#### システム管理

```bash
# ヘルスチェック
pmpl-agent health
```

### Python API経由での利用

```python
import asyncio
from pmpl_agent_system import PMPLAgentSystem

async def main():
    # システム初期化
    system = PMPLAgentSystem()
    
    # 議論開始
    session_id = await system.start_discussion(
        topic="エンジニア組織のスケーリング課題",
        organization_context={
            "company_size": 35,
            "industry": "FinTech",
            "development_stage": "急成長期",
            "current_challenges": ["採用", "技術的負債", "品質管理"]
        }
    )
    
    # レポート生成
    report = await system.generate_report(session_id)
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
```

## プロジェクト構造

```
pmpl-agent-system/
├── src/pmpl_agent_system/
│   ├── agents/           # エージェント実装
│   │   ├── coordinator.py   # メインコーディネーター
│   │   └── personas.py      # ペルソナエージェント
│   ├── config/           # 設定管理
│   │   └── settings.py      # 設定モデル
│   ├── core/             # コアシステム
│   │   └── system.py        # メインシステムクラス
│   ├── llm/              # LLM管理
│   │   └── manager.py       # LLMマネージャー
│   ├── models/           # データモデル
│   │   └── data.py          # Pydanticモデル
│   ├── storage/          # ストレージ
│   │   └── local.py         # ローカルファイルストレージ
│   └── cli.py            # CLIインターフェース
├── config/
│   └── default.yaml      # デフォルト設定
├── tests/                # テストコード
├── pyproject.toml        # プロジェクト設定
└── README.md            # このファイル
```

## 設定

### LLMプロバイダー設定

```yaml
system:
  default_llm:
    provider: "openai"
    model: "gpt-4o"
    temperature: 0.7

agents:
  coordinator:
    llm:
      provider: "openai" 
      model: "gpt-4o"
      temperature: 0.3
```

### エージェント別設定

各ペルソナエージェントに個別のLLM設定を適用可能：

```yaml
agents:
  startup_pm:
    llm:
      model: "gpt-4o-mini"
      temperature: 0.8
  enterprise_pm:
    llm:
      model: "gpt-4o-mini"
      temperature: 0.7
```

## 開発

### Docker開発環境（推奨）

```bash
# 開発環境を起動
make setup

# VSCode Dev Containerを使用
# 「Reopen in Container」を選択

# またはコンテナに直接入る
make shell

# テストを実行
make test

# リンターとフォーマットを実行
make lint
make format
```

### ローカル開発環境

```bash
# 開発依存関係をインストール
uv sync --extra dev

# pre-commitフックを設定
pre-commit install

# テスト実行
pytest

# 型チェック
pyright

# コードフォーマット
ruff format .

# linting
ruff check .
```

### 実装優先順位

現在の開発状況：

- ✅ **Phase 1**: 基本機能実装（LLMマネージャー、基本ペルソナ、議論フロー）
- 🚧 **Phase 2**: 高度機能（課題十分性判定、動的ペルソナ選定）
- ⏳ **Phase 3**: 品質向上（エラーハンドリング、ログ、テスト）
- ⏳ **Phase 4**: 運用準備（Docker化、CI/CD、ドキュメント）

## ライセンス

MIT License

## 貢献

プルリクエストや課題報告を歓迎します。開発に参加される場合は、事前にIssueで議論することをお勧めします。

## サポート

技術的な質問やバグ報告は、GitHubのIssueをご利用ください。 