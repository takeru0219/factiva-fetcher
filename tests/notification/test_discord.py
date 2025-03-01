import unittest
from unittest.mock import MagicMock, patch

from src.notification.discord import (
    _create_embed,
    send_notification,
)


class TestDiscordNotification(unittest.TestCase):
    """Discord通知機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 環境変数のモック
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/test",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.env_patcher.stop()

    @patch("src.notification.discord.requests.post")
    def test_send_notification_success(self, mock_post):
        """通知送信成功のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        # テストデータ
        test_data = {
            "title": "Test Title",
            "summary": "Test Summary",
            "topics": ["Topic 1", "Topic 2"],
            "sentiment": "positive",
            "facts": ["Fact 1", "Fact 2"],
            "related_entities": ["Entity 1", "Entity 2"],
            "source": "Test Source",
            "publication_date": "2023-01-01T00:00:00Z",
        }

        # テスト実行
        result = send_notification(test_data)

        # 検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "https://discord.com/api/webhooks/test")
        self.assertEqual(call_args[1]["headers"], {"Content-Type": "application/json"})
        self.assertTrue(result)

    @patch("src.notification.discord.requests.post")
    def test_send_notification_with_custom_webhook(self, mock_post):
        """カスタムWebhook URLでの通知送信テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        # テストデータ
        test_data = {"title": "Test Title"}
        custom_webhook = "https://discord.com/api/webhooks/custom"

        # テスト実行
        result = send_notification(test_data, webhook_url=custom_webhook)

        # 検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], custom_webhook)
        self.assertTrue(result)

    @patch("src.notification.discord.requests.post")
    def test_send_notification_failure(self, mock_post):
        """通知送信失敗のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # テストデータ
        test_data = {"title": "Test Title"}

        # テスト実行
        result = send_notification(test_data)

        # 検証
        mock_post.assert_called_once()
        self.assertFalse(result)

    @patch("src.notification.discord.requests.post")
    def test_send_notification_exception(self, mock_post):
        """通知送信例外のテスト"""
        # モックの設定
        mock_post.side_effect = Exception("Test error")

        # テストデータ
        test_data = {"title": "Test Title"}

        # テスト実行
        result = send_notification(test_data)

        # 検証
        mock_post.assert_called_once()
        self.assertFalse(result)

    def test_send_notification_no_webhook(self):
        """Webhook URLがない場合のテスト"""
        # 環境変数をクリア
        self.env_patcher.stop()
        self.env_patcher = patch.dict("os.environ", {})
        self.env_patcher.start()

        # テストデータ
        test_data = {"title": "Test Title"}

        # テスト実行
        result = send_notification(test_data)

        # 検証
        self.assertFalse(result)

    def test_create_embed(self):
        """Embedの作成テスト"""
        # テストデータ
        test_data = {
            "title": "Test Title",
            "summary": "Test Summary",
            "topics": ["Topic 1", "Topic 2"],
            "sentiment": "positive",
            "facts": ["Fact 1", "Fact 2"],
            "related_entities": ["Entity 1", "Entity 2"],
            "source": "Test Source",
            "publication_date": "2023-01-01T00:00:00Z",
            "url": "https://example.com/test",
        }

        # テスト実行
        embed = _create_embed(test_data)

        # 検証
        self.assertEqual(embed["title"], "Test Title")
        self.assertEqual(embed["description"], "Test Summary")
        self.assertEqual(embed["url"], "https://example.com/test")
        self.assertEqual(embed["color"], 0x00FF00)  # 緑色（ポジティブ）
        self.assertEqual(embed["timestamp"], "2023-01-01T00:00:00Z")
        self.assertEqual(embed["footer"]["text"], "Source: Test Source")

        # フィールドの検証
        fields = embed["fields"]
        self.assertEqual(len(fields), 4)  # トピック、感情、事実、エンティティ

        # トピックフィールド
        self.assertEqual(fields[0]["name"], "トピック")
        self.assertEqual(fields[0]["value"], "Topic 1, Topic 2")
        self.assertTrue(fields[0]["inline"])

        # 感情フィールド
        self.assertEqual(fields[1]["name"], "感情分析")
        self.assertEqual(fields[1]["value"], "ポジティブ 📈")
        self.assertTrue(fields[1]["inline"])

        # 事実フィールド
        self.assertEqual(fields[2]["name"], "重要な事実")
        self.assertEqual(fields[2]["value"], "• Fact 1\n• Fact 2")
        self.assertFalse(fields[2]["inline"])

        # エンティティフィールド
        self.assertEqual(fields[3]["name"], "関連エンティティ")
        self.assertEqual(fields[3]["value"], "Entity 1, Entity 2")
        self.assertFalse(fields[3]["inline"])

    def test_create_embed_negative_sentiment(self):
        """ネガティブ感情のEmbed作成テスト"""
        # テストデータ
        test_data = {
            "title": "Test Title",
            "summary": "Test Summary",
            "sentiment": "negative",
        }

        # テスト実行
        embed = _create_embed(test_data)

        # 検証
        self.assertEqual(embed["color"], 0xFF0000)  # 赤色（ネガティブ）

        # 感情フィールド
        sentiment_field = embed["fields"][1]
        self.assertEqual(sentiment_field["name"], "感情分析")
        self.assertEqual(sentiment_field["value"], "ネガティブ 📉")


if __name__ == "__main__":
    unittest.main()
