import logging
import os
from typing import Any, Dict, Iterator, Optional

from dnastreaming import DNAStreaming


class FactivaStreamer:
    """Factivaストリーミングデータを取得するクラス"""

    def __init__(
        self,
        user_id: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        stream_id: Optional[str] = None,
    ):
        """
        Factivaストリーマーの初期化

        Args:
            user_id: Factiva APIのユーザーID（未指定時は環境変数から取得）
            password: Factiva APIのパスワード（未指定時は環境変数から取得）
            client_id: Factiva APIのクライアントID（未指定時は環境変数から取得）
            client_secret: Factiva APIのクライアントシークレット（未指定時は環境変数から取得）
            stream_id: 購読するストリームID（未指定時は環境変数から取得）
        """
        self.logger = logging.getLogger(__name__)

        # 認証情報の設定
        self.user_id = user_id or os.environ.get("FACTIVA_USER_ID")
        self.password = password or os.environ.get("FACTIVA_PASSWORD")
        self.client_id = client_id or os.environ.get("FACTIVA_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("FACTIVA_CLIENT_SECRET")
        self.stream_id = stream_id or os.environ.get("FACTIVA_STREAM_ID")

        if not all(
            [
                self.user_id,
                self.password,
                self.client_id,
                self.client_secret,
                self.stream_id,
            ]
        ):
            raise ValueError(
                "Factiva API認証情報が不足しています。環境変数または初期化パラメータで指定してください。"
            )

        # DNAStreamingクライアントの初期化
        self.client = DNAStreaming(
            user_id=self.user_id,
            password=self.password,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        self.logger.info(
            f"FactivaStreamerが初期化されました。ストリームID: {self.stream_id}"
        )

    def stream(
        self, batch_size: int = 10, max_retries: int = 3
    ) -> Iterator[Dict[str, Any]]:
        """
        Factivaからのストリーミングデータを取得するジェネレータ

        Args:
            batch_size: 一度に取得するドキュメント数
            max_retries: 接続エラー時の最大リトライ回数

        Yields:
            Dict[str, Any]: 取得したドキュメントデータ
        """
        retry_count = 0

        while True:
            try:
                # ストリームに接続
                self.logger.info(f"ストリーム {self.stream_id} に接続しています...")

                # ストリームからデータを取得
                # 注意: 実際のAPIの使用方法はライブラリのドキュメントに従ってください
                documents = self.client.get_documents(
                    stream_id=self.stream_id, batch_size=batch_size
                )

                # 取得したドキュメントを1つずつ返す
                for doc in documents:
                    yield self._process_document(doc)

                # 成功したらリトライカウントをリセット
                retry_count = 0

            except Exception as e:
                retry_count += 1
                self.logger.error(f"ストリーミング中にエラーが発生しました: {str(e)}")

                if retry_count > max_retries:
                    self.logger.critical(
                        f"最大リトライ回数 ({max_retries}) を超えました。終了します。"
                    )
                    raise

                self.logger.info(f"リトライ {retry_count}/{max_retries}...")
                # リトライ前に少し待機
                import time

                time.sleep(5 * retry_count)  # 指数バックオフ

    def _process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        取得したドキュメントを処理する

        Args:
            document: Factivaから取得した生のドキュメントデータ

        Returns:
            Dict[str, Any]: 処理済みのドキュメントデータ
        """
        # ここでドキュメントの前処理を行う
        # 例: 不要なフィールドの削除、フォーマットの変換など

        # 処理例（実際のデータ構造に合わせて調整してください）
        processed = {
            "id": document.get("id") or document.get("documentId"),
            "title": document.get("title") or document.get("headline"),
            "body": document.get("body") or document.get("text"),
            "publication_date": document.get("publicationDate"),
            "source": document.get("source") or document.get("publication"),
            "metadata": {
                "language": document.get("language"),
                "subjects": document.get("subjects", []),
                "companies": document.get("companies", []),
                "regions": document.get("regions", []),
            },
            "raw_data": document,  # 元のデータも保持
        }

        self.logger.debug(f"ドキュメント処理完了: {processed['id']}")
        return processed

    def close(self):
        """ストリーミング接続を閉じる"""
        try:
            # 接続を閉じる処理（ライブラリの仕様に合わせて実装）
            if hasattr(self.client, "close"):
                self.client.close()
            self.logger.info("ストリーミング接続を閉じました")
        except Exception as e:
            self.logger.error(f"接続を閉じる際にエラーが発生しました: {str(e)}")


# 使用例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    streamer = FactivaStreamer()

    try:
        for document in streamer.stream():
            print(f"ドキュメント受信: {document['id']} - {document['title']}")
            # ここでドキュメントを処理
    except KeyboardInterrupt:
        print("ストリーミングを停止します...")
    finally:
        streamer.close()
