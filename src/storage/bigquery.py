import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# BigQueryクライアントのインポート
try:
    from google.cloud import bigquery
except ImportError:
    logging.warning(
        "google-cloud-bigqueryライブラリがインストールされていません。pip install google-cloud-bigquery でインストールしてください。"
    )

logger = logging.getLogger(__name__)

# BigQuery設定（環境変数から取得）
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
DATASET_ID = os.environ.get("BIGQUERY_DATASET", "factiva_data")
TABLE_ID = os.environ.get("BIGQUERY_TABLE", "articles")


def store_data(
    article_data: Dict[str, Any],
    analysis_data: Dict[str, Any],
    project_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
    table_id: Optional[str] = None,
) -> bool:
    """
    BigQueryにデータを保存する

    Args:
        article_data: 記事データ
        analysis_data: 分析結果データ
        project_id: GCPプロジェクトID（未指定時は環境変数から取得）
        dataset_id: BigQueryデータセットID（未指定時は環境変数から取得）
        table_id: BigQueryテーブルID（未指定時は環境変数から取得）

    Returns:
        bool: 保存成功時はTrue、失敗時はFalse
    """
    # 設定の取得
    project_id = project_id or PROJECT_ID
    dataset_id = dataset_id or DATASET_ID
    table_id = table_id or TABLE_ID

    if not project_id:
        logger.warning(
            "GCPプロジェクトIDが設定されていません。環境変数GOOGLE_CLOUD_PROJECTを設定してください。"
        )
        return False

    try:
        # BigQueryクライアントの初期化
        client = bigquery.Client(project=project_id)

        # データセットの参照
        dataset_ref = client.dataset(dataset_id)

        # テーブルの参照
        table_ref = dataset_ref.table(table_id)

        # データの準備
        row = _prepare_row(article_data, analysis_data)

        # データの挿入
        errors = client.insert_rows_json(table_ref, [row])

        if not errors:
            logger.info(f"データをBigQueryに保存しました: {row['id']}")
            return True
        else:
            logger.error(f"BigQueryへのデータ挿入中にエラーが発生しました: {errors}")
            return False

    except NameError:
        # BigQueryクライアントがインポートされていない場合
        logger.warning(
            "BigQueryクライアントがインポートされていないため、データは保存されません。"
        )
        _log_data(article_data, analysis_data)
        return False

    except Exception as e:
        logger.error(f"BigQueryへのデータ保存中にエラーが発生しました: {str(e)}")
        return False


def ensure_table_exists(
    project_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
    table_id: Optional[str] = None,
) -> bool:
    """
    BigQueryのテーブルが存在することを確認し、存在しない場合は作成する

    Args:
        project_id: GCPプロジェクトID（未指定時は環境変数から取得）
        dataset_id: BigQueryデータセットID（未指定時は環境変数から取得）
        table_id: BigQueryテーブルID（未指定時は環境変数から取得）

    Returns:
        bool: テーブルが存在するか作成された場合はTrue、それ以外はFalse
    """
    # 設定の取得
    project_id = project_id or PROJECT_ID
    dataset_id = dataset_id or DATASET_ID
    table_id = table_id or TABLE_ID

    if not project_id:
        logger.warning(
            "GCPプロジェクトIDが設定されていません。環境変数GOOGLE_CLOUD_PROJECTを設定してください。"
        )
        return False

    try:
        # BigQueryクライアントの初期化
        client = bigquery.Client(project=project_id)

        # データセットの参照
        dataset_ref = client.dataset(dataset_id)

        # データセットが存在するか確認
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            # データセットが存在しない場合は作成
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"  # ロケーションの設定
            dataset = client.create_dataset(dataset)
            logger.info(f"データセット {dataset_id} を作成しました")

        # テーブルの参照
        table_ref = dataset_ref.table(table_id)

        # テーブルが存在するか確認
        try:
            client.get_table(table_ref)
            logger.info(f"テーブル {table_id} は既に存在します")
            return True
        except Exception:
            # テーブルが存在しない場合は作成
            schema = _get_table_schema()
            table = bigquery.Table(table_ref, schema=schema)
            table = client.create_table(table)
            logger.info(f"テーブル {table_id} を作成しました")
            return True

    except NameError:
        # BigQueryクライアントがインポートされていない場合
        logger.warning(
            "BigQueryクライアントがインポートされていないため、テーブルの確認/作成はスキップされます。"
        )
        return False

    except Exception as e:
        logger.error(f"BigQueryテーブルの確認/作成中にエラーが発生しました: {str(e)}")
        return False


def _get_table_schema() -> List[bigquery.SchemaField]:
    """
    BigQueryテーブルのスキーマを定義する

    Returns:
        List[bigquery.SchemaField]: テーブルスキーマ
    """
    return [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED", description="記事ID"),
        bigquery.SchemaField("title", "STRING", description="記事タイトル"),
        bigquery.SchemaField("body", "STRING", description="記事本文"),
        bigquery.SchemaField("source", "STRING", description="情報ソース"),
        bigquery.SchemaField("publication_date", "TIMESTAMP", description="公開日時"),
        bigquery.SchemaField("url", "STRING", description="記事URL"),
        bigquery.SchemaField(
            "topics", "STRING", mode="REPEATED", description="トピック"
        ),
        bigquery.SchemaField("sentiment", "STRING", description="感情分析結果"),
        bigquery.SchemaField("summary", "STRING", description="要約"),
        bigquery.SchemaField(
            "facts", "STRING", mode="REPEATED", description="重要な事実"
        ),
        bigquery.SchemaField(
            "related_entities",
            "STRING",
            mode="REPEATED",
            description="関連エンティティ",
        ),
        bigquery.SchemaField("metadata", "JSON", description="メタデータ"),
        bigquery.SchemaField("processed_at", "TIMESTAMP", description="処理日時"),
    ]


def _prepare_row(
    article_data: Dict[str, Any], analysis_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    BigQueryに挿入するためのデータ行を準備する

    Args:
        article_data: 記事データ
        analysis_data: 分析結果データ

    Returns:
        Dict[str, Any]: BigQueryに挿入するデータ行
    """
    # 現在時刻
    now = datetime.utcnow().isoformat()

    # 記事データの取得
    article_id = article_data.get("id", "")
    title = article_data.get("title", "")
    body = article_data.get("body", "")
    source = article_data.get("source", "")
    publication_date = article_data.get("publication_date", "")
    url = article_data.get("url", "")

    # メタデータの準備
    metadata = article_data.get("metadata", {})
    if not metadata and "raw_data" in article_data:
        # raw_dataがある場合はそれをメタデータとして使用
        metadata = article_data["raw_data"]

    # 分析結果の取得
    topics = analysis_data.get("topics", [])
    sentiment = analysis_data.get("sentiment", "neutral")
    summary = analysis_data.get("summary", "")
    facts = analysis_data.get("facts", [])
    related_entities = analysis_data.get("related_entities", [])

    # データ行の作成
    return {
        "id": article_id,
        "title": title,
        "body": body,
        "source": source,
        "publication_date": publication_date,
        "url": url,
        "topics": topics,
        "sentiment": sentiment,
        "summary": summary,
        "facts": facts,
        "related_entities": related_entities,
        "metadata": json.dumps(metadata),
        "processed_at": now,
    }


def _log_data(article_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> None:
    """
    BigQueryが利用できない場合にデータをログに出力する（開発・デバッグ用）

    Args:
        article_data: 記事データ
        analysis_data: 分析結果データ
    """
    row = _prepare_row(article_data, analysis_data)
    logger.info(
        f"BigQueryに保存されるはずのデータ: {json.dumps(row, ensure_ascii=False)}"
    )


# テスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # テーブルの存在確認/作成
    ensure_table_exists()

    # テストデータ
    test_article = {
        "id": "test-doc-001",
        "title": "テスト記事タイトル",
        "body": "これはテスト用の記事本文です。BigQueryへの保存テストを行っています。",
        "source": "テストソース",
        "publication_date": "2023-01-01T00:00:00Z",
        "url": "https://example.com/test-article",
    }

    test_analysis = {
        "topics": ["ビジネス", "テクノロジー", "経済"],
        "sentiment": "positive",
        "summary": "これはテスト用の要約です。",
        "facts": ["テスト事実1", "テスト事実2"],
        "related_entities": ["テスト企業A", "テスト企業B"],
    }

    # データ保存
    success = store_data(test_article, test_analysis)
    print(f"データ保存結果: {'成功' if success else '失敗'}")
