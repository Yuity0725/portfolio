"""API境界: FastAPI ルーター + Pydantic コントローラ（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
Pydantic はこの「境界」だけで使い、検証済みの入力をユースケースへ渡す。応答は
ドメインエンティティ (``to_dict``) から Pydantic スキーマへ組み立てて返す。
フレームワーク型（Pydantic）を内側（usecase/domain）へ持ち込まないのが方針。

例では抽象化のため ``ExaminationUsecase`` をプロトコルとして受け取る。実際の結線は
application_usecase.py の合成ルートを参照。
"""

from __future__ import annotations

from typing import Optional, Protocol

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


# --- 境界スキーマ（Pydantic）: 検証・OpenAPI ドキュメント生成を担う ---
class ExaminationToCreateScheme(BaseModel):
    name: str = Field(..., description="試験種名", example="サンプル大学 全学部 2020年度 物理 第2問")
    question: str = Field(..., description="大問", example="第2問")
    year: int = Field(..., ge=1900, le=2100, description="出題年度", example=2020)
    max_marks: int = Field(..., ge=0, description="満点", example=50)
    man_hour: float = Field(..., ge=0, description="工数", example=0.08)
    branch_name: str = Field(..., description="校舎／支部名", example="サンプル大学")
    department_name: Optional[str] = Field(None, description="学部／区分", example="全学部")
    subject: str = Field(..., description="科目コード", example="physics")
    subject_number: Optional[int] = Field(None, description="科目通し番号", example=1)


class ExaminationUUIDScheme(BaseModel):
    uuid: str = Field(..., description="試験種のUUID")


class ExaminationScheme(ExaminationToCreateScheme, ExaminationUUIDScheme):
    """作成スキーマ + UUID の合成（レスポンス用）。"""


class ExaminationCollectionScheme(BaseModel):
    examinations: list[ExaminationScheme]


# --- ユースケースの型（実装は application 層で注入される） ---
class ExaminationUsecase(Protocol):
    def register_examination(self, **kwargs) -> str: ...
    def select_examination_by(self, examination_id: str): ...
    def list_examination(self) -> list: ...
    def delete_examination(self, uuid: str) -> None: ...


class NotFoundError(Exception):
    pass


# --- adapters/controllers: HTTP スキーマ ⇄ ユースケースの変換に専念 ---
class ExaminationController:
    def __init__(self, usecase: ExaminationUsecase) -> None:
        self.__usecase = usecase

    def create(self, to_create: ExaminationToCreateScheme) -> ExaminationUUIDScheme:
        uuid = self.__usecase.register_examination(**to_create.dict())
        return ExaminationUUIDScheme(uuid=uuid)

    def retrieve(self, examination_uuid: str) -> ExaminationScheme:
        try:
            entity = self.__usecase.select_examination_by(examination_uuid)
        except NotFoundError:
            raise HTTPException(status_code=404, detail="Not found")
        return ExaminationScheme.parse_obj(entity.to_dict())

    def list(self) -> ExaminationCollectionScheme:
        examinations = [ExaminationScheme.parse_obj(e.to_dict()) for e in self.__usecase.list_examination()]
        return ExaminationCollectionScheme(examinations=examinations)

    def delete(self, examination_uuid: str) -> dict:
        try:
            self.__usecase.delete_examination(examination_uuid)
        except NotFoundError:
            raise HTTPException(status_code=404, detail="Not found")
        return {"message": "success"}


# --- infrastructures/servers: ルーターの組み立て（薄く保つ） ---
def get_route(controller: ExaminationController) -> APIRouter:
    router = APIRouter(prefix="/api/v3/answer_db/examinations", tags=["examination"])

    @router.post("/", response_model=ExaminationUUIDScheme)
    def create_examination(to_create: ExaminationToCreateScheme) -> ExaminationUUIDScheme:
        return controller.create(to_create)

    @router.get("/{examination_uuid}", response_model=ExaminationScheme)
    def retrieve_examination(examination_uuid: str) -> ExaminationScheme:
        return controller.retrieve(examination_uuid)

    @router.get("/", response_model=ExaminationCollectionScheme)
    def list_examinations() -> ExaminationCollectionScheme:
        return controller.list()

    @router.delete("/{examination_uuid}")
    def delete_examination(examination_uuid: str) -> dict:
        return controller.delete(examination_uuid)

    return router
