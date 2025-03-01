import unittest
from unittest.mock import MagicMock, patch

from src.storage.bigquery import (
    _get_table_schema,
    _prepare_row,
    ensure_table_exists,
    store_data,
)


class TestBigQueryStorage(unittest.TestCase):
    """BigQueryデータ保存機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 環境変数のモック
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "GOOGLE_CLOUD_PROJECT": "test-project",
                "BIGQUERY_DATASET": "test_dataset",
                "BIGQUERY_TABLE": "test_table",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.env_patcher.stop()

    @patch("src.storage.bigquery.bigquery")
    def test_store_data_success(self, mock_bigquery):
        """データ保存成功のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client
        mock_client.insert_rows_json.return_value = []  # 空リストは成功を意味する

        # テストデータ
        test_article = {
            "id": "test-doc",
            "title": "Test Title",
            "body": "Test Body",
            "source": "Test Source",
            "publication_date": "2023-01-01T00:00:00Z",
        }
        test_analysis = {
            "topics": ["Topic 1", "Topic 2"],
            "sentiment": "positive",
            "summary": "Test Summary",
            "facts": ["Fact 1", "Fact 2"],
            "related_entities": ["Entity 1", "Entity 2"],
        }

        # テスト実行
        result = store_data(test_article, test_analysis)

        # 検証
        mock_bigquery.Client.assert_called_once_with(project="test-project")
        mock_client.dataset.assert_called_once_with("test_dataset")
        mock_client.insert_rows_json.assert_called_once()
        self.assertTrue(result)

    @patch("src.storage.bigquery.bigquery")
    def test_store_data_with_custom_params(self, mock_bigquery):
        """カスタムパラメータでのデータ保存テスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client
        mock_client.insert_rows_json.return_value = []

        # テストデータ
        test_article = {"id": "test-doc"}
        test_analysis = {"summary": "Test Summary"}

        # テスト実行
        result = store_data(
            test_article,
            test_analysis,
            project_id="custom-project",
            dataset_id="custom_dataset",
            table_id="custom_table",
        )

        # 検証
        mock_bigquery.Client.assert_called_once_with(project="custom-project")
        mock_client.dataset.assert_called_once_with("custom_dataset")
        self.assertTrue(result)

    @patch("src.storage.bigquery.bigquery")
    def test_store_data_failure(self, mock_bigquery):
        """データ保存失敗のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client
        mock_client.insert_rows_json.return_value = ["Error 1"]  # エラーがある場合

        # テストデータ
        test_article = {"id": "test-doc"}
        test_analysis = {"summary": "Test Summary"}

        # テスト実行
        result = store_data(test_article, test_analysis)

        # 検証
        mock_client.insert_rows_json.assert_called_once()
        self.assertFalse(result)

    @patch("src.storage.bigquery.bigquery")
    def test_store_data_exception(self, mock_bigquery):
        """データ保存例外のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client
        mock_client.insert_rows_json.side_effect = Exception("Test error")

        # テストデータ
        test_article = {"id": "test-doc"}
        test_analysis = {"summary": "Test Summary"}

        # テスト実行
        result = store_data(test_article, test_analysis)

        # 検証
        mock_client.insert_rows_json.assert_called_once()
        self.assertFalse(result)

    def test_store_data_no_project_id(self):
        """プロジェクトIDがない場合のテスト"""
        # 環境変数をクリア
        self.env_patcher.stop()
        self.env_patcher = patch.dict("os.environ", {})
        self.env_patcher.start()

        # テストデータ
        test_article = {"id": "test-doc"}
        test_analysis = {"summary": "Test Summary"}

        # テスト実行
        result = store_data(test_article, test_analysis)

        # 検証
        self.assertFalse(result)

    @patch("src.storage.bigquery.bigquery")
    def test_ensure_table_exists_table_exists(self, mock_bigquery):
        """テーブルが既に存在する場合のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client
        # テーブルが存在する場合は例外を発生させない
        mock_client.get_table.return_value = MagicMock()

        # テスト実行
        result = ensure_table_exists()

        # 検証
        mock_bigquery.Client.assert_called_once_with(project="test-project")
        mock_client.dataset.assert_called_once_with("test_dataset")
        mock_client.get_table.assert_called_once()
        mock_client.create_table.assert_not_called()  # テーブルは作成されない
        self.assertTrue(result)

    @patch("src.storage.bigquery.bigquery")
    def test_ensure_table_exists_create_table(self, mock_bigquery):
        """テーブルを作成する場合のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client
        # テーブルが存在しない場合は例外を発生させる
        mock_client.get_table.side_effect = Exception("Table not found")
        # データセットは存在する
        mock_client.get_dataset.return_value = MagicMock()

        # テスト実行
        result = ensure_table_exists()

        # 検証
        mock_bigquery.Client.assert_called_once_with(project="test-project")
        mock_client.dataset.assert_called_once_with("test_dataset")
        mock_client.get_table.assert_called_once()
        mock_client.create_table.assert_called_once()  # テーブルが作成される
        self.assertTrue(result)

    @patch("src.storage.bigquery.bigquery")
    def test_ensure_table_exists_create_dataset_and_table(self, mock_bigquery):
        """データセットとテーブルを作成する場合のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client
        # データセットもテーブルも存在しない場合は例外を発生させる
        mock_client.get_dataset.side_effect = Exception("Dataset not found")
        mock_client.get_table.side_effect = Exception("Table not found")

        # テスト実行
        result = ensure_table_exists()

        # 検証
        mock_bigquery.Client.assert_called_once_with(project="test-project")
        mock_client.dataset.assert_called_once_with("test_dataset")
        mock_client.get_dataset.assert_called_once()
        mock_client.create_dataset.assert_called_once()  # データセットが作成される
        mock_client.create_table.assert_called_once()  # テーブルが作成される
        self.assertTrue(result)

    @patch("src.storage.bigquery.bigquery")
    def test_get_table_schema(self, mock_bigquery):
        """テーブルスキーマ取得のテスト"""
        # モックの設定
        mock_schema_field = MagicMock()
        mock_bigquery.SchemaField = mock_schema_field

        # テスト実行
        schema = _get_table_schema()

        # 検証
        self.assertEqual(len(schema), 13)  # 13フィールド

        # SchemaFieldの呼び出し回数を検証
        self.assertEqual(mock_schema_field.call_count, 13)

        # いくつかの呼び出しを検証
        calls = mock_schema_field.call_args_list

        # id フィールド
        id_call = calls[0]
        self.assertEqual(id_call[0][0], "id")
        self.assertEqual(id_call[0][1], "STRING")
        self.assertEqual(id_call[1]["mode"], "REQUIRED")

        # title フィールド
        title_call = calls[1]
        self.assertEqual(title_call[0][0], "title")
        self.assertEqual(title_call[0][1], "STRING")

        # topics フィールド
        topics_call = calls[6]
        self.assertEqual(topics_call[0][0], "topics")
        self.assertEqual(topics_call[0][1], "STRING")
        self.assertEqual(topics_call[1]["mode"], "REPEATED")

    def test_prepare_row(self):
        """データ行準備のテスト"""
        # テストデータ
        test_article = {
            "id": "test-doc",
            "title": "Test Title",
            "body": "Test Body",
            "source": "Test Source",
            "publication_date": "2023-01-01T00:00:00Z",
            "url": "https://example.com/test",
            "metadata": {"language": "en"},
        }
        test_analysis = {
            "topics": ["Topic 1", "Topic 2"],
            "sentiment": "positive",
            "summary": "Test Summary",
            "facts": ["Fact 1", "Fact 2"],
            "related_entities": ["Entity 1", "Entity 2"],
        }

        # テスト実行
        row = _prepare_row(test_article, test_analysis)

        # 検証
        self.assertEqual(row["id"], "test-doc")
        self.assertEqual(row["title"], "Test Title")
        self.assertEqual(row["body"], "Test Body")
        self.assertEqual(row["source"], "Test Source")
        self.assertEqual(row["publication_date"], "2023-01-01T00:00:00Z")
        self.assertEqual(row["url"], "https://example.com/test")
        self.assertEqual(row["topics"], ["Topic 1", "Topic 2"])
        self.assertEqual(row["sentiment"], "positive")
        self.assertEqual(row["summary"], "Test Summary")
        self.assertEqual(row["facts"], ["Fact 1", "Fact 2"])
        self.assertEqual(row["related_entities"], ["Entity 1", "Entity 2"])
        self.assertIn("metadata", row)
        self.assertIn("processed_at", row)


if __name__ == "__main__":
    unittest.main()
