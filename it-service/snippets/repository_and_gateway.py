"""依存性逆転: ドメインの抽象インターフェース + SQLAlchemy 実装（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
ドメイン層は抽象ゲートウェイ (``ExaminationDBGatewayInterface``) にのみ依存し、
永続化の詳細（SQLAlchemy）は adapter 層に隔離する。Repository は抽象型のクラス属性
を保持し、具体実装はユースケースから注入される（→ application_usecase.py 参照）。

実際にはこれらは別ファイル（domains/interfaces, domains, adapters/db_gateways）に
分かれているが、対応関係を示すため 1 ファイルにまとめている。
"""

from __future__ import annotations

import abc
from typing import Optional

from sqlalchemy.engine.base import Connectable
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import Float, Integer, String

from domain_models import Branch, Department, ExamSubject, Examination, Subject

Base = declarative_base()


class NotFoundError(Exception):
    """該当レコードが存在しないことを表すドメイン寄りの例外。"""


# --- domains/interfaces: ドメインが定義する抽象（依存の向きはここへ内向き） ---
class ExaminationDBGatewayInterface(metaclass=abc.ABCMeta):
    """試験種の永続化ゲートウェイ。実装の詳細はドメインから隠蔽される。"""

    @abc.abstractmethod
    def retrieve(self, examination_id: str) -> Examination:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[Examination]:
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, examination: Examination) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, examination_id: str) -> None:
        raise NotImplementedError


# --- domains: Repository は抽象にのみ依存する ---
class ExaminationRepository:
    """ドメイン向けの永続化ファサード。具体ゲートウェイは外から注入される。"""

    db_gateway: ExaminationDBGatewayInterface

    @classmethod
    def select_by(cls, examination_id: str) -> Examination:
        return cls.db_gateway.retrieve(examination_id)

    @classmethod
    def list(cls) -> list[Examination]:
        return cls.db_gateway.list()

    @classmethod
    def save(cls, examination: Examination) -> str:
        return cls.db_gateway.create(examination)

    @classmethod
    def delete(cls, examination_id: str) -> None:
        cls.db_gateway.delete(examination_id)


# --- adapters/db_gateways: SQLAlchemy による具体実装 ---
class ExaminationModel(Base):
    """ORM モデル。ドメインエンティティとは別物として扱い、相互変換する。"""

    __tablename__ = "examination"

    uuid = Column(String(36), primary_key=True)
    name = Column(String(64), nullable=False)
    question = Column(String(64), nullable=False)
    year = Column(Integer, nullable=False)
    max_marks = Column(Integer, nullable=False)
    man_hour = Column(Float, nullable=False)
    branch_name = Column(String(64), nullable=False)
    department = Column(String(64), nullable=True)
    subject = Column(String(32), nullable=False)
    subject_number = Column(Integer, nullable=True)

    @classmethod
    def from_entity(cls, examination: Examination) -> "ExaminationModel":
        """ドメインエンティティ → ORM モデル。"""
        return cls(
            uuid=examination.uuid,
            name=examination.name,
            question=examination.question,
            year=examination.year,
            max_marks=examination.max_marks,
            man_hour=examination.man_hour,
            branch_name=examination.branch.name,
            department=examination.department.name if examination.department else None,
            subject=examination.exam_subject.subject.value,
            subject_number=examination.exam_subject.number,
        )

    def to_entity(self) -> Examination:
        """ORM モデル → ドメインエンティティ。DB スキーマの都合をドメインへ持ち込まない。"""
        return Examination(
            uuid=self.uuid,
            name=self.name,
            question=self.question,
            year=self.year,
            max_marks=self.max_marks,
            man_hour=self.man_hour,
            branch=Branch(id=0, name=self.branch_name),
            department=Department(self.department) if self.department else None,
            exam_subject=ExamSubject(subject=Subject(self.subject), number=self.subject_number),
        )


class ExaminationDBGateway(ExaminationDBGatewayInterface):
    """抽象インターフェースを満たす SQLAlchemy 実装。"""

    def __init__(self, engine: Connectable) -> None:
        ExaminationModel.metadata.bind = engine
        self.__session = sessionmaker(engine)()

    def retrieve(self, examination_id: str) -> Examination:
        model: Optional[ExaminationModel] = self.__session.query(ExaminationModel).get(examination_id)
        if model is None:
            raise NotFoundError
        return model.to_entity()

    def list(self) -> list[Examination]:
        models: list[ExaminationModel] = self.__session.query(ExaminationModel).all()
        return [model.to_entity() for model in models]

    def create(self, examination: Examination) -> str:
        model = ExaminationModel.from_entity(examination)
        self.__session.add(model)
        self.__session.commit()
        return model.uuid

    def delete(self, examination_id: str) -> None:
        model: Optional[ExaminationModel] = self.__session.query(ExaminationModel).get(examination_id)
        if model is None:
            raise NotFoundError
        self.__session.delete(model)
        self.__session.commit()
