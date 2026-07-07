"""SQS→Lambda ワーカーのエントリポイント骨子（技術デモ用の匿名サンプル）。

技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
(illustrative demo authored for this portfolio; not production source).

設計意図:
- 1つのワーカーエントリが、メッセージ本文の `worker` 種別を見て
  対応ハンドラへディスパッチする（ハンドラ追加だけで新ジョブ種別に対応）。
- SQSイベントは生dictのまま扱わず、型付きモデルへパースしてから渡す。
- 認証情報やキュー名などは環境変数参照のみ（値はコードに書かない）。
"""

from __future__ import annotations

import json
from typing import Any, Callable, Protocol

from pydantic import BaseModel, Field, ValidationError


class WorkerMessage(BaseModel):
    """SQSメッセージ本文の共通スキーマ。境界でバリデーションする。"""

    worker: str = Field(..., description="ディスパッチ先のハンドラ種別")
    staff_id: str = Field(..., description="投入者のスタッフ識別子(JWTクレーム由来)")
    payload: dict[str, Any] = Field(default_factory=dict)


class Handler(Protocol):
    """各ワーカーハンドラが満たすインターフェース。"""

    def __call__(self, message: WorkerMessage) -> None: ...


def _handle_return_answer_sheets(message: WorkerMessage) -> None:
    """答案の一括返却（実処理は内部POS API連携。ここでは骨子のみ）。"""
    # 例: message.payload["targets"] を1件ずつ処理する
    ...


def _handle_process_answer_images(message: WorkerMessage) -> None:
    """答案画像の処理（OpenCV/pdf2image/pyzbar等。ここでは骨子のみ）。"""
    ...


# worker 種別 → ハンドラ の対応表。ここに1行足すだけで拡張できる。
HANDLERS: dict[str, Handler] = {
    "return_answer_sheets": _handle_return_answer_sheets,
    "process_answer_images": _handle_process_answer_images,
}


def handler(event: dict, _context: object) -> dict:
    """Lambdaエントリポイント。バッチで受け取り、レコードごとに処理する。

    1レコードでも部分的に失敗し得るため、部分バッチ応答
    (batchItemFailures) を返し、失敗分だけをSQSへ再表示させる。
    """
    failures: list[str] = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "")
        try:
            message = WorkerMessage.model_validate(json.loads(record["body"]))
        except (ValidationError, KeyError, json.JSONDecodeError):
            failures.append(message_id)
            continue

        target: Callable[[WorkerMessage], None] | None = HANDLERS.get(message.worker)
        if target is None:
            # 未知の worker 種別は再処理しても直らないため、握りつぶす代わりに記録する
            failures.append(message_id)
            continue

        try:
            target(message)
        except Exception:  # noqa: BLE001 - 個別失敗のみ部分再処理へ回す
            failures.append(message_id)

    return {"batchItemFailures": [{"itemIdentifier": mid} for mid in failures]}
