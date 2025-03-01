import unittest
from unittest.mock import MagicMock, patch

from src.pubsub.publisher import (
    get_topic_path,
    publish_message,
)


class TestPublisher(unittest.TestCase):
    """Pub/Sub発行機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 環境変数のモック
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "GOOGLE_CLOUD_PROJECT": "test-project",
                "PUBSUB_TOPIC": "test-topic",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.env_patcher.stop()

    @patch("src.pubsub.publisher.publisher")
    def test_get_topic_path(self, mock_publisher):
        """トピックパス取得のテスト"""
        # モックの設定
        mock_publisher.topic_path.return_value = (
            "projects/test-project/topics/test-topic"
        )

        # テスト実行
        result = get_topic_path()

        # 検証
        mock_publisher.topic_path.assert_called_once_with("test-project", "test-topic")
        self.assertEqual(result, "projects/test-project/topics/test-topic")

    @patch("src.pubsub.publisher.publisher")
    def test_get_topic_path_with_params(self, mock_publisher):
        """パラメータ指定でのトピックパス取得のテスト"""
        # モックの設定
        mock_publisher.topic_path.return_value = (
            "projects/custom-project/topics/custom-topic"
        )

        # テスト実行
        result = get_topic_path("custom-topic", "custom-project")

        # 検証
        mock_publisher.topic_path.assert_called_once_with(
            "custom-project", "custom-topic"
        )
        self.assertEqual(result, "projects/custom-project/topics/custom-topic")

    @patch("src.pubsub.publisher.publisher")
    def test_get_topic_path_missing_project(self, mock_publisher):
        """プロジェクトIDが不足している場合のテスト"""
        # 環境変数をクリア
        self.env_patcher.stop()
        self.env_patcher = patch.dict("os.environ", {})
        self.env_patcher.start()

        # テスト実行
        with self.assertRaises(ValueError):
            get_topic_path()

    @patch("src.pubsub.publisher.publisher")
    def test_publish_message(self, mock_publisher):
        """メッセージ発行のテスト"""
        # モックの設定
        mock_future = MagicMock()
        mock_future.result.return_value = "test-message-id"
        mock_publisher.publish.return_value = mock_future
        mock_publisher.topic_path.return_value = (
            "projects/test-project/topics/test-topic"
        )

        # テストデータ
        test_data = {
            "id": "test-doc",
            "title": "Test Title",
            "body": "Test Body",
        }
        test_attributes = {"content_type": "article"}

        # テスト実行
        result = publish_message(test_data, attributes=test_attributes)

        # 検証
        mock_publisher.topic_path.assert_called_once_with("test-project", "test-topic")
        mock_publisher.publish.assert_called_once()
        # 引数の検証（データはJSON文字列に変換されるため、完全一致ではなく部分一致で検証）
        call_args = mock_publisher.publish.call_args
        self.assertEqual(call_args[0][0], "projects/test-project/topics/test-topic")
        self.assertIn(b"test-doc", call_args[1]["data"])
        self.assertIn(b"Test Title", call_args[1]["data"])
        self.assertEqual(call_args[1]["content_type"], "article")
        self.assertEqual(result, "test-message-id")

    @patch("src.pubsub.publisher.publisher")
    def test_publish_message_error(self, mock_publisher):
        """メッセージ発行エラーのテスト"""
        # モックの設定
        mock_publisher.publish.side_effect = Exception("Test error")
        mock_publisher.topic_path.return_value = (
            "projects/test-project/topics/test-topic"
        )

        # テストデータ
        test_data = {"id": "test-doc"}

        # テスト実行
        with self.assertRaises(Exception):
            publish_message(test_data)

        # 検証
        mock_publisher.topic_path.assert_called_once_with("test-project", "test-topic")
        mock_publisher.publish.assert_called_once()


if __name__ == "__main__":
    unittest.main()
