.PHONY: help build up down logs shell test lint format clean

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo "  build      - Docker イメージをビルド"
	@echo "  up         - 開発環境を起動"
	@echo "  down       - 開発環境を停止"
	@echo "  logs       - ログを表示"
	@echo "  shell      - コンテナ内でシェルを起動"
	@echo "  test       - テストを実行"
	@echo "  lint       - リンターを実行"
	@echo "  format     - コードフォーマットを実行"
	@echo "  clean      - 停止済みコンテナとイメージを削除"
	@echo "  prod-up    - 本番環境を起動"
	@echo "  prod-down  - 本番環境を停止"

# Docker イメージをビルド
build:
	docker compose build pmpl-agent

# 開発環境を起動
up:
	docker compose up -d pmpl-agent

# 開発環境を停止
down:
	docker compose down

# ログを表示
logs:
	docker compose logs -f pmpl-agent

# コンテナ内でシェルを起動
shell:
	docker compose exec pmpl-agent bash

# テストを実行（コンテナ内で）
test:
	docker compose exec pmpl-agent pytest

# リンターを実行（コンテナ内で）
lint:
	docker compose exec pmpl-agent ruff check src/ tests/

# コードフォーマットを実行（コンテナ内で）
format:
	docker compose exec pmpl-agent ruff format src/ tests/

# 停止済みコンテナとイメージを削除
clean:
	docker compose down --rmi all --volumes --remove-orphans

# 本番環境を起動
prod-up:
	docker compose --profile production up -d pmpl-agent-prod

# 本番環境を停止
prod-down:
	docker compose --profile production down

# 初回セットアップ
setup:
	@echo "🚀 PMPL Agent System のDocker環境をセットアップしています..."
	docker compose build pmpl-agent
	docker compose up -d pmpl-agent
	@echo "✅ セットアップ完了! 'make shell' でコンテナに入れます" 