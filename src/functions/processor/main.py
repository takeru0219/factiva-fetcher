from src.analysis.llm import analyze_content
from src.notification.discord import send_notification
from src.storage.bigquery import store_data


def process_pubsub_message(event, context):
    """Pub/Subからのメッセージを処理するCloud Function"""

    # メッセージデータの取得
    pubsub_message = event.get("data")

    # LLMによる分析
    analysis_result = analyze_content(pubsub_message)

    # Discord通知
    send_notification(analysis_result)

    # BigQueryに保存
    store_data(pubsub_message, analysis_result)

    return "OK"
