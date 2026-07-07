"""FastAPI + SSEストリーミングのLambdaハンドラ骨子（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
FastAPIアプリをそのままLambdaで実行し（Lambda Web Adapter / Mangum）、
API GatewayのレスポンスストリーミングでRAG応答をSSE配信する構成を示す。
認証情報は値を持たず、必ず環境変数から参照する。
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="RAG Chat API (demo)")


class GenerateRequest(BaseModel):
    """RAG生成リクエスト。"""

    question: str = Field(..., min_length=1, description="ユーザーの質問")


class GeminiClient:
    """LLMクライアントの薄いラッパ（デモ用スタブ）。

    実運用ではAPIキーを環境変数から取得し、外部に値をハードコードしない。
    """

    def __init__(self) -> None:
        # 機密はコードに埋め込まず環境変数参照とする
        self._api_key: str = os.environ["GEMINI_API_KEY"]

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """トークンを逐次生成する（デモではプレースホルダ）。"""
        for chunk in ["…", "回答", "を", "生成", "します"]:
            yield chunk


async def build_context(question: str) -> str:
    """検索結果からプロンプト用コンテキストを構築する（デモでは省略）。"""
    # 実運用では OpenSearch 検索 → スコアリング・重複除去 → 文脈連結
    return f"[context for] {question}"


def _to_sse(token: str) -> str:
    """1トークンをSSEフレームに整形する。"""
    return f"data: {token}\n\n"


@app.post("/generate")
async def generate(request: GenerateRequest) -> StreamingResponse:
    """質問を受け取り、RAG応答をSSEでストリーミングする。"""
    client = GeminiClient()

    async def event_stream() -> AsyncIterator[str]:
        context = await build_context(request.question)
        prompt = f"{context}\n\nQ: {request.question}"
        async for token in client.stream(prompt):
            yield _to_sse(token)
        yield _to_sse("[DONE]")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Lambda Web Adapter 経由ではこの `app` をそのまま起動する。
# Mangum を使う場合の例:
#   from mangum import Mangum
#   handler = Mangum(app)
