FROM python:3.9-slim

WORKDIR /app

# poetryの設定ファイルとロックファイルをコピー
COPY poetry.lock pyproject.toml ./

# poetryをインストールし、依存関係をインストール
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# アプリケーションコードをコピー
COPY . .

# Cloud Runでは環境変数PORT（デフォルト8080）でポートを指定
ENV PORT=8080

# アプリケーションの起動
CMD ["python", "-m", "src.api.main"]