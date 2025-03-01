import unittest
from unittest.mock import MagicMock, patch

from src.api.streamer import FactivaStreamer


class TestFactivaStreamer(unittest.TestCase):
    """FactivaStreamerクラスのテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 環境変数のモック
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "FACTIVA_USER_ID": "test_user",
                "FACTIVA_PASSWORD": "test_password",
                "FACTIVA_CLIENT_ID": "test_client_id",
                "FACTIVA_CLIENT_SECRET": "test_client_secret",
                "FACTIVA_STREAM_ID": "test_stream_id",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.env_patcher.stop()

    @patch("src.api.streamer.DNAStreaming")
    def test_init_with_env_vars(self, mock_dna_streaming):
        """環境変数から認証情報を取得して初期化するテスト"""
        # テスト実行
        streamer = FactivaStreamer()

        # 検証
        mock_dna_streaming.assert_called_once_with(
            user_id="test_user",
            password="test_password",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        self.assertEqual(streamer.stream_id, "test_stream_id")

    @patch("src.api.streamer.DNAStreaming")
    def test_init_with_params(self, mock_dna_streaming):
        """パラメータから認証情報を取得して初期化するテスト"""
        # テスト実行
        streamer = FactivaStreamer(
            user_id="param_user",
            password="param_password",
            client_id="param_client_id",
            client_secret="param_client_secret",
            stream_id="param_stream_id",
        )

        # 検証
        mock_dna_streaming.assert_called_once_with(
            user_id="param_user",
            password="param_password",
            client_id="param_client_id",
            client_secret="param_client_secret",
        )
        self.assertEqual(streamer.stream_id, "param_stream_id")

    @patch("src.api.streamer.DNAStreaming")
    def test_init_missing_credentials(self, mock_dna_streaming):
        """認証情報が不足している場合のテスト"""
        # 環境変数をクリア
        self.env_patcher.stop()
        self.env_patcher = patch.dict("os.environ", {})
        self.env_patcher.start()

        # テスト実行
        with self.assertRaises(ValueError):
            FactivaStreamer()

    @patch("src.api.streamer.DNAStreaming")
    def test_stream(self, mock_dna_streaming):
        """ストリーミングデータ取得のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_dna_streaming.return_value = mock_client

        # モックドキュメントの設定
        mock_docs = [
            {
                "id": "doc1",
                "title": "Test Title 1",
                "body": "Test Body 1",
                "publicationDate": "2023-01-01T00:00:00Z",
                "source": "Test Source 1",
                "language": "en",
                "subjects": ["Business"],
                "companies": ["Test Company"],
                "regions": ["US"],
            },
            {
                "id": "doc2",
                "title": "Test Title 2",
                "body": "Test Body 2",
                "publicationDate": "2023-01-02T00:00:00Z",
                "source": "Test Source 2",
                "language": "ja",
                "subjects": ["Technology"],
                "companies": ["Another Company"],
                "regions": ["JP"],
            },
        ]
        mock_client.get_documents.return_value = mock_docs

        # テスト実行
        streamer = FactivaStreamer()
        results = list(streamer.stream(batch_size=2, max_retries=1))

        # 検証
        mock_client.get_documents.assert_called_once_with(
            stream_id="test_stream_id", batch_size=2
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "doc1")
        self.assertEqual(results[0]["title"], "Test Title 1")
        self.assertEqual(results[1]["id"], "doc2")
        self.assertEqual(results[1]["title"], "Test Title 2")

    @patch("src.api.streamer.DNAStreaming")
    def test_process_document(self, mock_dna_streaming):
        """ドキュメント処理のテスト"""
        # テスト用ドキュメント
        test_doc = {
            "id": "test-doc",
            "title": "Test Title",
            "body": "Test Body",
            "publicationDate": "2023-01-01T00:00:00Z",
            "source": "Test Source",
            "language": "en",
            "subjects": ["Business", "Technology"],
            "companies": ["Test Company"],
            "regions": ["US", "JP"],
        }

        # テスト実行
        streamer = FactivaStreamer()
        result = streamer._process_document(test_doc)

        # 検証
        self.assertEqual(result["id"], "test-doc")
        self.assertEqual(result["title"], "Test Title")
        self.assertEqual(result["body"], "Test Body")
        self.assertEqual(result["publication_date"], "2023-01-01T00:00:00Z")
        self.assertEqual(result["source"], "Test Source")
        self.assertEqual(result["metadata"]["language"], "en")
        self.assertEqual(result["metadata"]["subjects"], ["Business", "Technology"])
        self.assertEqual(result["metadata"]["companies"], ["Test Company"])
        self.assertEqual(result["metadata"]["regions"], ["US", "JP"])
        self.assertEqual(result["raw_data"], test_doc)

    @patch("src.api.streamer.DNAStreaming")
    def test_close(self, mock_dna_streaming):
        """接続を閉じるテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_dna_streaming.return_value = mock_client

        # テスト実行
        streamer = FactivaStreamer()
        streamer.close()

        # 検証
        mock_client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
