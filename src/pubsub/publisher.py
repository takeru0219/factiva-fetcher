import json
import logging
import os
from typing import Any, Dict, Optional

from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)

# Pub/Subトピック名（環境変数から取得、デフォルト値はfactiva-data）
DEFAULT_TOPIC = os.environ.get("PUBSUB_TOPIC", "factiva-data")
# プロジェクトID（環境変数から取得）
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")

if not PROJECT_ID:
    logger.warning(
        "GOOGLE_CLOUD_PROJECT環境変数が設定されていません。ローカル開発環境では問題ありませんが、"
        "本番環境では必ず設定してください。"
    )

# Pub/Subパブリッシャークライアント
publisher = pubsub_v1.PublisherClient()


def get_topic_path(
    topic_name: str = DEFAULT_TOPIC, project_id: Optional[str] = PROJECT_ID
) -> str:
    """
    Pub/Subトピックのフルパスを取得する

    Args:
        topic_name: トピック名
        project_id: GCPプロジェクトID

    Returns:
        str: トピックのフルパス
    """
    if not project_id:
        raise ValueError(
            "GCPプロジェクトIDが設定されていません。環境変数GOOGLE_CLOUD_PROJECTを設定してください。"
        )

    return publisher.topic_path(project_id, topic_name)


def publish_message(
    data: Dict[str, Any],
    topic_name: str = DEFAULT_TOPIC,
    project_id: Optional[str] = PROJECT_ID,
    attributes: Optional[Dict[str, str]] = None,
) -> str:
    """
    Pub/Subトピックにメッセージを発行する

    Args:
        data: 発行するデータ（JSON形式に変換されます）
        topic_name: 発行先のトピック名
        project_id: GCPプロジェクトID
        attributes: メッセージに付与する属性（オプション）

    Returns:
        str: 発行されたメッセージのID
    """
    topic_path = get_topic_path(topic_name, project_id)

    # データをJSON形式にエンコード
    data_json = json.dumps(data, ensure_ascii=False)
    data_bytes = data_json.encode("utf-8")

    # 属性がない場合は空の辞書を使用
    attributes = attributes or {}

    try:
        # メッセージを発行
        future = publisher.publish(topic_path, data=data_bytes, **attributes)
        message_id = future.result()  # 発行完了を待機

        logger.info(
            f"メッセージを発行しました。ID: {message_id}, トピック: {topic_name}"
        )
        return message_id

    except Exception as e:
        logger.error(f"メッセージの発行に失敗しました: {str(e)}")
        raise


# ローカルテスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # テストデータ
    test_data = {
        "id": "test-document-001",
        "title": "テストドキュメント",
        "body": "これはテスト用のドキュメントです。",
        "publication_date": "2023-01-01T00:00:00Z",
        "source": "テストソース",
    }

    # テスト属性
    test_attributes = {"content_type": "article", "language": "ja"}

    # メッセージを発行
    message_id = publish_message(data=test_data, attributes=test_attributes)

    print(f"テストメッセージを発行しました。ID: {message_id}")
