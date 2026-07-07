"""アプリケーション層のユースケース + 合成ルート（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
ユースケースはドメインを協調させるだけで、永続化の詳細は知らない。抽象ゲートウェイ
を Repository に注入するのがこの層の責務。末尾の ``main`` は各コンテキストの
合成ルート（composition root）で、「ゲートウェイ → ユースケース → コントローラ →
ルーター」を一箇所で結線する（依存の組み立てを集約）。
"""

from __future__ import annotations

import uuid as uuid_lib
from typing import Optional

from sqlalchemy.engine.base import Connectable

from domain_models import Branch, Department, ExamSubject, Examination, Subject
from repository_and_gateway import (
    ExaminationDBGateway,
    ExaminationDBGatewayInterface,
    ExaminationRepository,
)
from router_and_controller import ExaminationController, get_route


class ExaminationBuilder:
    """生成(new)と再構築(reconstruct_from)を分けてエンティティを組み立てる Builder。"""

    def new(
        self,
        name: str,
        question: str,
        year: int,
        max_marks: int,
        man_hour: float,
        branch_name: str,
        department_name: Optional[str],
        subject: str,
        subject_number: Optional[int] = None,
    ) -> Examination:
        return Examination(
            uuid=str(uuid_lib.uuid4()),
            name=name,
            question=question,
            year=year,
            max_marks=max_marks,
            man_hour=man_hour,
            branch=Branch(id=0, name=branch_name),
            department=Department(department_name) if department_name else None,
            exam_subject=ExamSubject(subject=Subject(subject), number=subject_number),
        )


class ExaminationUsecase:
    """試験種に関するアプリケーションサービス。

    コンストラクタで具体ゲートウェイを Repository に注入する（依存性注入）。
    以降、ユースケースは Repository（＝抽象）越しにしか永続化に触れない。
    """

    def __init__(self, db_gateway: ExaminationDBGatewayInterface) -> None:
        ExaminationRepository.db_gateway = db_gateway
        self.__builder = ExaminationBuilder()

    def register_examination(
        self,
        name: str,
        question: str,
        year: int,
        max_marks: int,
        man_hour: float,
        branch_name: str,
        department_name: Optional[str] = None,
        subject: str = "math",
        subject_number: Optional[int] = None,
    ) -> str:
        examination = self.__builder.new(
            name=name,
            question=question,
            year=year,
            max_marks=max_marks,
            man_hour=man_hour,
            branch_name=branch_name,
            department_name=department_name,
            subject=subject,
            subject_number=subject_number,
        )
        return ExaminationRepository.save(examination)

    def select_examination_by(self, examination_id: str) -> Examination:
        return ExaminationRepository.select_by(examination_id)

    def list_examination(self) -> list[Examination]:
        return ExaminationRepository.list()

    def delete_examination(self, uuid: str) -> None:
        ExaminationRepository.delete(uuid)


def main(engine: Connectable):
    """コンテキストの合成ルート。依存を結線して FastAPI ルーターを返す。

    元プロジェクトでは各コンテキストの ``__init__.py`` がこの役割を担い、
    ``main.py`` が全コンテキストのルーターを ``include_router`` で束ねる。
    """
    controller = ExaminationController(
        ExaminationUsecase(ExaminationDBGateway(engine)),
    )
    return get_route(controller)
