.PHONY: test test-api test-pubsub test-analysis test-notification test-storage test-functions deploy-cloudrun deploy-functions

# テスト実行コマンド
test:
	# すべてのテストを実行
	python -m pytest tests/ -v

test-api:
	# APIモジュールのテストを実行
	python -m pytest tests/api/ -v

test-pubsub:
	# Pub/Subモジュールのテストを実行
	python -m pytest tests/pubsub/ -v

test-analysis:
	# 分析モジュールのテストを実行
	python -m pytest tests/analysis/ -v

test-notification:
	# 通知モジュールのテストを実行
	python -m pytest tests/notification/ -v

test-storage:
	# ストレージモジュールのテストを実行
	python -m pytest tests/storage/ -v

test-functions:
	# Cloud Functionsモジュールのテストを実行
	python -m pytest tests/functions/ -v

# 開発環境セットアップ
setup-dev:
	# 開発環境のセットアップ
	poetry install
	cp .env.sample .env
	@echo "開発環境のセットアップが完了しました。.envファイルを編集して必要な環境変数を設定してください。"

# デプロイコマンド
deploy-cloudrun:
	# コンテナのビルドとデプロイ
	gcloud builds submit --tag gcr.io/[PROJECT_ID]/factiva-streamer
	gcloud run deploy factiva-streamer \
	--image gcr.io/[PROJECT_ID]/factiva-streamer \
	--platform managed \
	--memory 1Gi \
	--timeout 3600 \
	--set-env-vars="FACTIVA_USER_ID=your_user_id,FACTIVA_PASSWORD=your_password,..."

deploy-functions:
	# Pub/Subトリガー用Cloud Functionのデプロイ
	gcloud functions deploy process_pubsub_message \
	--runtime python39 \
	--trigger-topic factiva-data \
	--source src/functions/processor \
	--entry-point process_pubsub_message \
	--memory 512MB \
	--timeout 300s \
	--set-env-vars="OPENAI_API_KEY=your_openai_api_key,DISCORD_WEBHOOK_URL=your_discord_webhook_url,..."