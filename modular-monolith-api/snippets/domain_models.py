"""ドメイン層の Value Object / Entity（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
ドメイン層はフレームワークに依存せず、標準の dataclass で表現する、という
プロジェクト方針を示す。不変の値は ``frozen=True`` の Value Object とし、
同一性を持つものは Entity とする。識別子・名称はすべて一般化したプレースホルダ。
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Optional


class Subject(enum.Enum):
    """科目 <value object>。

    表示名ではなく安定したコード値を保持し、外部境界での変換に耐えるようにする。
    """

    MATH = "math"
    ENGLISH = "english"
    JAPANESE = "japanese"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    # ... 実際にはより多くの科目を扱う（ここでは代表のみ）


@dataclasses.dataclass(frozen=True)
class Branch:
    """校舎／支部 <value object>。

    元プロジェクトでは特定企業の拠点区分を表す値オブジェクトだったが、
    ここでは中立的な「支部（branch/campus）」として一般化している。
    """

    id: int
    name: str


@dataclasses.dataclass(frozen=True)
class Examiner:
    """添削者（採点担当者）<value object>。

    同一性は外部の staff ID に委ねるため、ここでは不変値として扱う。
    """

    id: str
    name: str


@dataclasses.dataclass(frozen=True)
class Department:
    """出題単位（学部/区分）<value object>。"""

    name: str


@dataclasses.dataclass(frozen=True)
class ExamSubject:
    """科目 + 通し番号の組 <value object>。"""

    subject: Subject
    number: Optional[int] = None


@dataclasses.dataclass(frozen=False)
class Examination:
    """試験種 <entity>。

    UUID による同一性を持つ。工数(man_hour) など業務上の値を保持し、
    境界層向けの素な dict へ変換するメソッドを提供する。
    """

    uuid: str
    name: str
    question: str
    year: int
    max_marks: int
    man_hour: float
    branch: Branch
    department: Optional[Department]
    exam_subject: ExamSubject

    def is_recent(self, from_year: int) -> bool:
        """指定年度以降の出題かどうか、という小さなドメイン判定の例。"""
        return self.year >= from_year

    def to_dict(self) -> dict:
        """境界層（コントローラ）へ渡すための素なマッピング。"""
        return {
            "uuid": self.uuid,
            "name": self.name,
            "question": self.question,
            "year": self.year,
            "max_marks": self.max_marks,
            "man_hour": self.man_hour,
            "branch_name": self.branch.name,
            "department_name": self.department.name if self.department else None,
            "subject": self.exam_subject.subject.value,
            "subject_number": self.exam_subject.number,
        }
