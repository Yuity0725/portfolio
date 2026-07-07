"""答案返却リクエストの型付きDRFシリアライザ（技術デモ用の匿名サンプル）。

技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
(illustrative demo authored for this portfolio; not production source).

方針:
- APIの入力検証は「enqueueやジョブ投入の前」にシリアライザへ集約し、
  不正な要求はそもそも非同期処理へ流さない（fail-closed）。
- スタッフ識別子は本文ではなく、検証済みCognitoクレーム由来の値を採用する。
"""

from __future__ import annotations

from rest_framework import serializers


class ReturnTargetSerializer(serializers.Serializer):
    """返却対象の答案1件を表す。"""

    answer_sheet_id = serializers.CharField(max_length=64)
    scheduled_return_date = serializers.DateField()

    def validate_answer_sheet_id(self, value: str) -> str:
        """答案IDは英数字のみ（内部フォーマットの前提を境界で担保）。"""
        if not value.isalnum():
            raise serializers.ValidationError("answer_sheet_id must be alphanumeric")
        return value


class ReturnRequestSerializer(serializers.Serializer):
    """一括返却リクエスト。ここを通ったものだけをSQS/ジョブへ渡す。"""

    MAX_TARGETS = 1000

    targets = ReturnTargetSerializer(many=True)
    notify_slack = serializers.BooleanField(default=False)

    def validate_targets(self, value: list[dict]) -> list[dict]:
        """空・過大・重複を入口で弾く。"""
        if not value:
            raise serializers.ValidationError("targets must not be empty")
        if len(value) > self.MAX_TARGETS:
            raise serializers.ValidationError(
                f"targets must be <= {self.MAX_TARGETS} per request",
            )
        ids = [t["answer_sheet_id"] for t in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("targets contain duplicate answer_sheet_id")
        return value

    def to_worker_message(self, staff_id: str) -> dict:
        """検証済みデータを、非同期ワーカー向けメッセージ本文へ整形する。

        staff_id は request 本文ではなく、検証済みJWTクレームから渡す
        （所有者スコープと監査を一貫させるため）。
        """
        data = self.validated_data
        return {
            "worker": "return_answer_sheets",
            "staff_id": staff_id,
            "notify_slack": data["notify_slack"],
            "targets": [
                {
                    "answer_sheet_id": t["answer_sheet_id"],
                    "scheduled_return_date": t["scheduled_return_date"].isoformat(),
                }
                for t in data["targets"]
            ],
        }
