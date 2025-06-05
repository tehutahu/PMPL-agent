# Python 3.11を使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# pip を最新版にアップグレード
RUN pip install --upgrade pip

# pyproject.tomlとソースコードをコピー
COPY pyproject.toml README.md ./
COPY src/ ./src/

# 依存関係をインストール（開発用を含む）
RUN pip install -e ".[dev]"

# ポート8000を公開（FastAPI用）
EXPOSE 8000

# デフォルトコマンド
CMD ["bash"] 