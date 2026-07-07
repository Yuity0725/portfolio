"""OpenAI互換ローカルLLMから構造化出力を型安全に受け取るクライアントのデモ。

Illustrative demo for this portfolio — NOT the production source.
All endpoints and schemas are placeholders.
ポートフォリオ用の説明デモです。実運用ソースではありません。
エンドポイント・スキーマはすべてプレースホルダです。

ポイント:
- `response_format=json_schema` でサーバ側の制約デコード（GBNF）を有効化し、
  スキーマ準拠をデコード時に強制する（プロンプトで「JSONで返して」と頼まない）
- 応答は必ず Pydantic の `model_validate_json` でバインドし、生JSONを辞書のまま扱わない
"""

import asyncio

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# nginx LB（データ並列レプリカ構成）のエンドポイント。API keyはローカルでは未使用
LLAMA_SERVER_URL = "http://203.0.113.10:8080/v1"
MODEL_NAME = "example-30b-a3b-q4_k_m"


class CategoryScore(BaseModel):
    """1つの分類カテゴリとその確信度。"""

    category: str = Field(
        description="分類カテゴリ名",
        examples=["会議・議事録", "計画・方針"],
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="モデルの確信度（0〜1）",
        examples=[0.92],
    )


class ClassificationResult(BaseModel):
    """文書1件に対するマルチラベル分類結果。"""

    categories: list[CategoryScore] = Field(
        min_length=1,
        description="該当するカテゴリのリスト（1件以上）",
    )


async def classify(client: AsyncOpenAI, document_text: str) -> ClassificationResult:
    """文書を分類し、スキーマ準拠が保証された型付き結果を返す。"""
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            # systemプロンプトは固定内容にしてプレフィックスキャッシュを効かせる
            {"role": "system", "content": "あなたは文書分類器です。..."},
            {"role": "user", "content": document_text},
        ],
        # サーバ側でJSON Schema → GBNF文法に変換され、準拠出力のみ生成される
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "classification_result",
                "schema": ClassificationResult.model_json_schema(),
            },
        },
        temperature=0.0,
    )
    # 制約デコード済みでも、境界では必ずPydanticでバインドして型を確定させる
    return ClassificationResult.model_validate_json(
        response.choices[0].message.content or ""
    )


async def main() -> None:
    # ローカルサーバは認証不要のためダミー値（SDKの必須引数を満たすだけ）
    client = AsyncOpenAI(base_url=LLAMA_SERVER_URL, api_key="x")
    result = await classify(client, "（分類対象の文書テキスト）")
    for item in result.categories:
        print(f"{item.category}: {item.confidence:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
