import logging
import os
from typing import Any, Dict, Optional

# 使用するLLM APIに応じてインポートを変更
# 例: OpenAI APIを使用する場合
try:
    import openai

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
except ImportError:
    logging.warning(
        "openaiライブラリがインストールされていません。pip install openai でインストールしてください。"
    )

# 他のLLM APIを使用する場合はここに追加
# 例: Google Vertex AIを使用する場合
# from google.cloud import aiplatform

logger = logging.getLogger(__name__)


def analyze_content(
    data: Dict[str, Any], model: Optional[str] = None
) -> Dict[str, Any]:
    """
    LLMを使用してFactivaから取得したデータを分析する

    Args:
        data: 分析するデータ
        model: 使用するLLMモデル（未指定時はデフォルト値を使用）

    Returns:
        Dict[str, Any]: 分析結果
    """
    # デフォルトモデルの設定
    model = model or os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

    # 分析対象のテキスト抽出
    title = data.get("title", "")
    body = data.get("body", "")
    source = data.get("source", "")
    publication_date = data.get("publication_date", "")

    # 分析用のプロンプト作成
    prompt = f"""
以下のニュース記事を分析し、以下の情報を抽出してください：
1. 主要トピック（3つまで）
2. 感情分析（ポジティブ/ニュートラル/ネガティブ）
3. 重要な事実や数字
4. 関連する業界や企業
5. 記事の要約（100単語以内）

記事タイトル: {title}
出典: {source}
日付: {publication_date}

記事本文:
{body}
"""

    try:
        # OpenAI APIを使用した分析
        if "OPENAI_API_KEY" in os.environ:
            return _analyze_with_openai(prompt, model)

        # 他のLLM APIを使用する場合はここに追加
        # 例: Google Vertex AIを使用する場合
        # if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        #     return _analyze_with_vertex_ai(prompt, model)

        # APIキーが設定されていない場合はモック結果を返す
        logger.warning("LLM APIキーが設定されていません。モック結果を返します。")
        return _mock_analysis_result(data)

    except Exception as e:
        logger.error(f"分析中にエラーが発生しました: {str(e)}")
        # エラー時はシンプルな結果を返す
        return {
            "error": str(e),
            "topics": [],
            "sentiment": "neutral",
            "facts": [],
            "related_entities": [],
            "summary": f"分析エラー: {title}",
        }


def _analyze_with_openai(prompt: str, model: str) -> Dict[str, Any]:
    """
    OpenAI APIを使用してテキストを分析する

    Args:
        prompt: 分析用のプロンプト
        model: 使用するモデル

    Returns:
        Dict[str, Any]: 分析結果
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
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

        # レスポンスからテキストを抽出
        analysis_text = response.choices[0].message.content

        # テキストから構造化データを抽出
        # 注: 実際の実装ではより堅牢なパース処理が必要
        topics = []
        sentiment = "neutral"
        facts = []
        related_entities = []
        summary = ""

        # 簡易的なパース処理（実際の実装ではより堅牢な方法を使用）
        lines = analysis_text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "主要トピック" in line:
                current_section = "topics"
            elif "感情分析" in line:
                current_section = "sentiment"
                if "ポジティブ" in line.lower():
                    sentiment = "positive"
                elif "ネガティブ" in line.lower():
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
            elif "重要な事実" in line or "数字" in line:
                current_section = "facts"
            elif "関連する業界" in line or "企業" in line:
                current_section = "entities"
            elif "要約" in line:
                current_section = "summary"
            elif current_section == "topics" and line.startswith("-"):
                topics.append(line.lstrip("- "))
            elif current_section == "facts" and line.startswith("-"):
                facts.append(line.lstrip("- "))
            elif current_section == "entities" and line.startswith("-"):
                related_entities.append(line.lstrip("- "))
            elif current_section == "summary" and not line.startswith("#"):
                summary += line + " "

        return {
            "topics": topics[:3],  # 最大3つまで
            "sentiment": sentiment,
            "facts": facts,
            "related_entities": related_entities,
            "summary": summary.strip(),
            "raw_analysis": analysis_text,
        }

    except Exception as e:
        logger.error(f"OpenAI APIでの分析中にエラーが発生しました: {str(e)}")
        raise


def _mock_analysis_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    モックの分析結果を生成する（開発・テスト用）

    Args:
        data: 元のデータ

    Returns:
        Dict[str, Any]: モックの分析結果
    """
    title = data.get("title", "")

    return {
        "topics": ["ビジネス", "テクノロジー", "経済"],
        "sentiment": "neutral",
        "facts": [
            "これはモックの分析結果です",
            "実際のLLM分析を行うには、APIキーを設定してください",
        ],
        "related_entities": ["モック企業", "テスト産業"],
        "summary": f"これは「{title}」のモック要約です。実際のLLM分析を行うには、環境変数にAPIキーを設定してください。",
        "is_mock": True,
    }


# テスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # テストデータ
    test_data = {
        "id": "test-doc-001",
        "title": "テスト記事タイトル",
        "body": "これはテスト用の記事本文です。LLM分析のテストを行っています。",
        "source": "テストソース",
        "publication_date": "2023-01-01T00:00:00Z",
    }

    # 分析実行
    result = analyze_content(test_data)

    # 結果表示
    print("分析結果:")
    print(f"トピック: {result['topics']}")
    print(f"感情: {result['sentiment']}")
    print(f"事実: {result['facts']}")
    print(f"関連エンティティ: {result['related_entities']}")
    print(f"要約: {result['summary']}")
