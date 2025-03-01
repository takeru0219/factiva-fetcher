import json
import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Discord Webhook URL（環境変数から取得）
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def send_notification(data: Dict[str, Any], webhook_url: Optional[str] = None) -> bool:
    """
    Discordに通知を送信する

    Args:
        data: 送信するデータ
        webhook_url: Discord Webhook URL（未指定時は環境変数から取得）

    Returns:
        bool: 送信成功時はTrue、失敗時はFalse
    """
    # Webhook URLの設定
    webhook_url = webhook_url or DISCORD_WEBHOOK_URL

    if not webhook_url:
        logger.warning(
            "Discord Webhook URLが設定されていません。環境変数DISCORD_WEBHOOK_URLを設定してください。"
        )
        return False

    try:
        # 分析結果からメッセージを作成
        embed = _create_embed(data)

        # Discordに送信
        payload = {"embeds": [embed]}
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )

        # レスポンスの確認
        if response.status_code == 204:
            logger.info("Discordへの通知が成功しました")
            return True
        else:
            logger.error(
                f"Discordへの通知が失敗しました: ステータスコード {response.status_code}, "
                f"レスポンス {response.text}"
            )
            return False

    except Exception as e:
        logger.error(f"Discordへの通知中にエラーが発生しました: {str(e)}")
        return False


def _create_embed(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Discord用のembedを作成する

    Args:
        data: 分析結果データ

    Returns:
        Dict[str, Any]: Discord embed形式のデータ
    """
    # 元の記事データの取得（存在する場合）
    original_data = data.get("raw_data", {})

    # 記事情報
    title = original_data.get("title") or data.get("title", "タイトルなし")
    url = original_data.get("url") or data.get("url", "")
    source = original_data.get("source") or data.get("source", "不明")
    publication_date = original_data.get("publication_date") or data.get(
        "publication_date", ""
    )

    # 分析結果
    topics = data.get("topics", [])
    sentiment = data.get("sentiment", "neutral")
    summary = data.get("summary", "要約なし")

    # 感情に応じた色の設定
    color = 0x0099FF  # デフォルト: 青
    if sentiment == "positive":
        color = 0x00FF00  # 緑
    elif sentiment == "negative":
        color = 0xFF0000  # 赤

    # Embedの作成
    embed = {
        "title": title,
        "description": summary,
        "url": url,
        "color": color,
        "timestamp": publication_date,
        "footer": {"text": f"Source: {source}"},
        "fields": [],
    }

    # トピックの追加
    if topics:
        embed["fields"].append(
            {"name": "トピック", "value": ", ".join(topics), "inline": True}
        )

    # 感情の追加
    sentiment_text = "ニュートラル"
    if sentiment == "positive":
        sentiment_text = "ポジティブ 📈"
    elif sentiment == "negative":
        sentiment_text = "ネガティブ 📉"

    embed["fields"].append(
        {"name": "感情分析", "value": sentiment_text, "inline": True}
    )

    # 重要な事実の追加
    facts = data.get("facts", [])
    if facts:
        facts_text = "\n".join([f"• {fact}" for fact in facts[:3]])
        embed["fields"].append(
            {"name": "重要な事実", "value": facts_text, "inline": False}
        )

    # 関連エンティティの追加
    entities = data.get("related_entities", [])
    if entities:
        embed["fields"].append(
            {"name": "関連エンティティ", "value": ", ".join(entities), "inline": False}
        )

    return embed


# テスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # テストデータ
    test_data = {
        "title": "テスト記事タイトル",
        "summary": "これはテスト用の要約です。実際の分析結果ではありません。",
        "topics": ["ビジネス", "テクノロジー", "経済"],
        "sentiment": "positive",
        "facts": [
            "これはテスト用の事実1です",
            "これはテスト用の事実2です",
            "これはテスト用の事実3です",
        ],
        "related_entities": ["テスト企業A", "テスト企業B", "テスト産業"],
        "source": "テストソース",
        "publication_date": "2023-01-01T00:00:00Z",
    }

    # テスト用のWebhook URL（実際のURLに置き換えてください）
    test_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if test_webhook_url:
        # 通知送信
        success = send_notification(test_data, test_webhook_url)
        print(f"通知送信結果: {'成功' if success else '失敗'}")
    else:
        print("テストを実行するには環境変数DISCORD_WEBHOOK_URLを設定してください")
