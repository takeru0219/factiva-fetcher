import unittest
from unittest.mock import MagicMock, patch

from src.analysis.llm import (
    _analyze_with_openai,
    _mock_analysis_result,
    analyze_content,
)


class TestLLMAnalysis(unittest.TestCase):
    """LLM分析機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 環境変数のモック
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-api-key",
                "LLM_MODEL": "gpt-3.5-turbo",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.env_patcher.stop()

    @patch("src.analysis.llm._analyze_with_openai")
    def test_analyze_content_with_openai(self, mock_analyze_with_openai):
        """OpenAI APIを使用した分析のテスト"""
        # モックの設定
        mock_analyze_with_openai.return_value = {
            "topics": ["Business", "Technology"],
            "sentiment": "positive",
            "facts": ["Fact 1", "Fact 2"],
            "related_entities": ["Company A", "Industry B"],
            "summary": "This is a test summary.",
            "raw_analysis": "Full analysis text...",
        }

        # テストデータ
        test_data = {
            "id": "test-doc",
            "title": "Test Title",
            "body": "Test Body",
            "source": "Test Source",
            "publication_date": "2023-01-01T00:00:00Z",
        }

        # テスト実行
        result = analyze_content(test_data)

        # 検証
        mock_analyze_with_openai.assert_called_once()
        self.assertEqual(result["topics"], ["Business", "Technology"])
        self.assertEqual(result["sentiment"], "positive")
        self.assertEqual(result["facts"], ["Fact 1", "Fact 2"])
        self.assertEqual(result["related_entities"], ["Company A", "Industry B"])
        self.assertEqual(result["summary"], "This is a test summary.")

    @patch("src.analysis.llm.openai")
    def test_analyze_with_openai(self, mock_openai):
        """OpenAI APIの呼び出しテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""
主要トピック:
- ビジネス
- テクノロジー
- 経済

感情分析: ポジティブ

重要な事実や数字:
- 事実1
- 事実2

関連する業界や企業:
- 企業A
- 業界B

記事の要約:
これはテスト要約です。
"""
                )
            )
        ]
        mock_openai.ChatCompletion.create.return_value = mock_response

        # テスト実行
        prompt = "テスト用プロンプト"
        result = _analyze_with_openai(prompt, "gpt-3.5-turbo")

        # 検証
        mock_openai.ChatCompletion.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはニュース記事を分析するアシスタントです。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        self.assertEqual(result["topics"], ["ビジネス", "テクノロジー", "経済"])
        self.assertEqual(result["sentiment"], "positive")
        self.assertEqual(result["facts"], ["事実1", "事実2"])
        self.assertEqual(result["related_entities"], ["企業A", "業界B"])
        self.assertEqual(result["summary"], "これはテスト要約です。")

    @patch("src.analysis.llm.openai")
    def test_analyze_with_openai_error(self, mock_openai):
        """OpenAI API呼び出しエラーのテスト"""
        # モックの設定
        mock_openai.ChatCompletion.create.side_effect = Exception("API error")

        # テスト実行
        with self.assertRaises(Exception):
            _analyze_with_openai("テスト用プロンプト", "gpt-3.5-turbo")

    def test_mock_analysis_result(self):
        """モック分析結果のテスト"""
        # テストデータ
        test_data = {
            "id": "test-doc",
            "title": "Test Title",
            "body": "Test Body",
        }

        # テスト実行
        result = _mock_analysis_result(test_data)

        # 検証
        self.assertIn("topics", result)
        self.assertIn("sentiment", result)
        self.assertIn("facts", result)
        self.assertIn("related_entities", result)
        self.assertIn("summary", result)
        self.assertTrue(result["is_mock"])
        self.assertIn("Test Title", result["summary"])

    @patch("src.analysis.llm._mock_analysis_result")
    def test_analyze_content_no_api_key(self, mock_mock_analysis):
        """API keyがない場合のテスト"""
        # 環境変数をクリア
        self.env_patcher.stop()
        self.env_patcher = patch.dict("os.environ", {})
        self.env_patcher.start()

        # モックの設定
        mock_result = {
            "topics": ["Mock Topic"],
            "sentiment": "neutral",
            "summary": "Mock summary",
            "is_mock": True,
        }
        mock_mock_analysis.return_value = mock_result

        # テストデータ
        test_data = {"title": "Test Title"}

        # テスト実行
        result = analyze_content(test_data)

        # 検証
        mock_mock_analysis.assert_called_once_with(test_data)
        self.assertEqual(result, mock_result)


if __name__ == "__main__":
    unittest.main()
