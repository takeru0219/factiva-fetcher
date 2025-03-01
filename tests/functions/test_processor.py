import unittest
from unittest.mock import MagicMock, patch

from src.functions.processor.main import process_pubsub_message


class TestProcessorFunction(unittest.TestCase):
    """Cloud Functions処理機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        pass

    def tearDown(self):
        """テスト後のクリーンアップ"""
        pass

    @patch("src.functions.processor.main.analyze_content")
    @patch("src.functions.processor.main.send_notification")
    @patch("src.functions.processor.main.store_data")
    def test_process_pubsub_message(
        self, mock_store_data, mock_send_notification, mock_analyze_content
    ):
        """Pub/Subメッセージ処理のテスト"""
        # モックの設定
        mock_analyze_content.return_value = {
            "topics": ["Topic 1", "Topic 2"],
            "sentiment": "positive",
            "summary": "Test Summary",
        }
        mock_send_notification.return_value = True
        mock_store_data.return_value = True

        # テストデータ
        test_event = {
            "data": {
                "id": "test-doc",
                "title": "Test Title",
                "body": "Test Body",
            }
        }
        test_context = MagicMock()

        # テスト実行
        result = process_pubsub_message(test_event, test_context)

        # 検証
        mock_analyze_content.assert_called_once_with(test_event.get("data"))
        mock_send_notification.assert_called_once_with(
            mock_analyze_content.return_value
        )
        mock_store_data.assert_called_once_with(
            test_event.get("data"), mock_analyze_content.return_value
        )
        self.assertEqual(result, "OK")

    @patch("src.functions.processor.main.analyze_content")
    @patch("src.functions.processor.main.send_notification")
    @patch("src.functions.processor.main.store_data")
    def test_process_pubsub_message_with_base64_data(
        self, mock_store_data, mock_send_notification, mock_analyze_content
    ):
        """Base64エンコードされたPub/Subメッセージ処理のテスト"""
        # モックの設定
        mock_analyze_content.return_value = {"summary": "Test Summary"}
        mock_send_notification.return_value = True
        mock_store_data.return_value = True

        # Base64エンコードされたデータ（実際のCloud Functionsの挙動をシミュレート）
        # eyJpZCI6InRlc3QtZG9jIiwidGl0bGUiOiJUZXN0IFRpdGxlIn0= は
        # {"id":"test-doc","title":"Test Title"} をBase64エンコードしたもの
        test_event = {"data": "eyJpZCI6InRlc3QtZG9jIiwidGl0bGUiOiJUZXN0IFRpdGxlIn0="}
        test_context = MagicMock()

        # テスト実行
        with patch("src.functions.processor.main.base64") as mock_base64:
            # Base64デコードのモック
            mock_base64.b64decode.return_value = (
                b'{"id":"test-doc","title":"Test Title"}'
            )
            mock_base64.b64decode.side_effect = (
                lambda x: b'{"id":"test-doc","title":"Test Title"}'
            )

            result = process_pubsub_message(test_event, test_context)

        # 検証
        # 注: 実際のコードでBase64デコードが実装されていない場合は、
        # このテストは失敗します。その場合は実装を追加する必要があります。
        mock_analyze_content.assert_called_once()
        mock_send_notification.assert_called_once_with(
            mock_analyze_content.return_value
        )
        mock_store_data.assert_called_once()
        self.assertEqual(result, "OK")

    @patch("src.functions.processor.main.analyze_content")
    @patch("src.functions.processor.main.send_notification")
    @patch("src.functions.processor.main.store_data")
    def test_process_pubsub_message_no_data(
        self, mock_store_data, mock_send_notification, mock_analyze_content
    ):
        """データがないPub/Subメッセージ処理のテスト"""
        # テストデータ
        test_event = {}  # dataフィールドなし
        test_context = MagicMock()

        # テスト実行
        result = process_pubsub_message(test_event, test_context)

        # 検証
        mock_analyze_content.assert_called_once_with(None)  # Noneが渡される
        mock_send_notification.assert_called_once_with(
            mock_analyze_content.return_value
        )
        mock_store_data.assert_called_once_with(None, mock_analyze_content.return_value)
        self.assertEqual(result, "OK")

    @patch("src.functions.processor.main.analyze_content")
    @patch("src.functions.processor.main.send_notification")
    @patch("src.functions.processor.main.store_data")
    def test_process_pubsub_message_analyze_error(
        self, mock_store_data, mock_send_notification, mock_analyze_content
    ):
        """分析エラー時のテスト"""
        # モックの設定
        mock_analyze_content.side_effect = Exception("Analysis error")

        # テストデータ
        test_event = {"data": {"id": "test-doc"}}
        test_context = MagicMock()

        # テスト実行
        with self.assertRaises(Exception):
            process_pubsub_message(test_event, test_context)

        # 検証
        mock_analyze_content.assert_called_once()
        mock_send_notification.assert_not_called()
        mock_store_data.assert_not_called()

    @patch("src.functions.processor.main.analyze_content")
    @patch("src.functions.processor.main.send_notification")
    @patch("src.functions.processor.main.store_data")
    def test_process_pubsub_message_notification_error(
        self, mock_store_data, mock_send_notification, mock_analyze_content
    ):
        """通知エラー時のテスト"""
        # モックの設定
        mock_analyze_content.return_value = {"summary": "Test Summary"}
        mock_send_notification.return_value = False  # 通知失敗

        # テストデータ
        test_event = {"data": {"id": "test-doc"}}
        test_context = MagicMock()

        # テスト実行
        result = process_pubsub_message(test_event, test_context)

        # 検証
        mock_analyze_content.assert_called_once()
        mock_send_notification.assert_called_once()
        mock_store_data.assert_called_once()  # 通知失敗でも保存は実行される
        self.assertEqual(result, "OK")


if __name__ == "__main__":
    unittest.main()
