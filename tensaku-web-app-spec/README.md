# Answer-Grading Web App — Contract-First Spec / 答案採点Webアプリ 契約ファースト仕様

> A contract-first specification for an online answer-sheet grading (答案添削/採点) web app: the REST API and data schema are defined **before** implementation, with a typed partial-credit scoring model.
>
> オンライン答案採点（答案添削）Webアプリの**契約ファースト**設計。REST API とデータスキーマを実装より先に定義し、部分点採点モデルを型で表現する。

> **Note / 注記**
> This is a **portfolio case study**. To protect commercial IP, no proprietary source code is published here — the repository contains design write-ups and **hand-authored, anonymized snippets** that illustrate the engineering.
> これは**ポートフォリオ用のケーススタディ**です。商用IP保護のため実プロダクトのソースは掲載していません。掲載コードはすべて**技術デモ用に書き起こした匿名サンプル**です。

---

## English (Summary)

A **contract-first** design for a web app where graders score scanned answer sheets (PDF/image) online. Instead of coding first and reconciling later, the project defines the **REST API contract (OpenAPI)** and the **message/data contract (Protocol Buffers)** up front, then models the **partial-credit scoring** logic as small, immutable, type-hinted Python objects.

The hard part of this domain is data shape, not volume: questions form a tree (large question → sub-questions), each leaf carries a scoring rubric (exclusive **addition groups** + **deductions**), and every score/mark/comment has a **position** on the sheet. A single ambiguous field breaks both the frontend and the grading logic — so the contract comes first.

**Highlights**
- **Contract-first design** — OpenAPI 3.0 REST contract + Protobuf message schema as the single source of truth, enabling parallel frontend/backend development and end-to-end type alignment.
- **Typed partial-credit scoring model** — recursive question tree, exclusive addition groups, deductions, and score clamping, expressed as frozen (immutable) Python value objects.
- **Positional metadata** — a typed coordinate model for where the score / mark / comment is rendered on each answer sheet page.
- **Schema-driven quality** — explicit enums, required/optional boundaries, and static type checking to keep contract and code from drifting.

See **[TECH_STACK.md](TECH_STACK.md)** for the stack, **[ARCHITECTURE.md](ARCHITECTURE.md)** for the contract/scoring model diagram, and **[features/](features/README.md)** for the deep-dives.

---

## 日本語（詳細）

### これは何か

採点者が、スキャンした答案（PDF/画像）をオンラインで採点するWebアプリの**契約ファースト仕様**です。先に実装して後からすり合わせるのではなく、**REST APIの契約（OpenAPI）**と**メッセージ/データの契約（Protocol Buffers）**を最初に定義し、その上で**部分点採点**ロジックを小さく不変な型付きオブジェクトとして設計しました。

このドメインの難しさはデータ量ではなく**データ構造**にあります。設問はツリー構造（大問→小問）を持ち、各末端の設問には採点基準（排他的な**加点グループ**と**減点**）が紐づき、点数・採点記号・コメントにはそれぞれ答案上の**座標**があります。1つの曖昧なフィールドがフロントと採点ロジックの双方を壊すため、**契約を先に固める**方針を採りました。

### 解決した課題 → アプローチ

| 課題 | アプローチ |
| --- | --- |
| 複雑な採点データ構造をフロント/バックで齟齬なく共有したい | **OpenAPI**でREST契約、**Protobuf**でデータ契約を先に定義し、単一の真実の源（SSOT）とする |
| フロントとバックを並行開発したい | 契約を起点に、フロントはモック/生成型、バックは同じ契約に沿って独立実装 |
| 記述式の部分点採点が複雑で壊れやすい | 採点モデルを**不変な値オブジェクト**として型設計。加点グループ（排他）＋減点＋上限クランプを明示 |
| 点数・記号・コメントを答案の正しい位置に描画したい | ページ＋座標を持つ**位置情報モデル（Position）**を型で表現 |
| 契約とコードが乖離しないようにしたい | 列挙型・required/optionalの明示・静的型チェックで境界の型整合を担保 |

### 主要機能

1. **契約ファースト設計** — OpenAPI（REST契約）＋ Protobuf（データ契約）を先に定義し、並行開発と型整合を担保（→ [features/01](features/01-contract-first-design.md)）
2. **部分点採点モデル** — 設問ツリー・加点グループ（排他）・減点・上限クランプを型で表現した採点ロジック（→ [features/02](features/02-partial-credit-scoring.md)）
3. **位置情報モデル** — 点数/採点記号/コメントの描画位置（ページ・座標）を型で保持

### 技術的な工夫（抜粋）

- **契約を単一の真実の源（SSOT）に** — OpenAPIとProtobufで境界のスキーマを先に確定し、フロント/バックの並行開発と型整合を両立
- **採点モデルの型設計** — `frozen` dataclass による不変な値オブジェクトで、加点グループの排他性・減点・満点クランプを表現 → [snippets/partial_credit_scorer.py](snippets/partial_credit_scorer.py)
- **言語非依存のデータ契約** — Protobufメッセージで設問・採点基準・座標を定義し、実装言語に依存しない型付きスキーマを提供 → [snippets/question.proto](snippets/question.proto)
- **曖昧さの排除** — 設問形式（選択式/短答式/自由記述/回答不可）を列挙型で固定し、required/optionalを契約で明示

### 担当領域

API/データ契約の設計から、採点ドメインモデルの型設計までを担当（OpenAPIスキーマ、Protobufスキーマ、Pythonドメインモデル）。

---

## Repository layout / このリポジトリの構成

```
tensaku-web-app-spec/
├── README.md            # 本書 / this file
├── ARCHITECTURE.md      # 契約・採点モデル図（Mermaid）/ contract & scoring model diagram
├── TECH_STACK.md        # 技術スタック一覧 / tech stack table
├── features/            # 各機能の工夫点 / per-feature deep-dives
│   ├── README.md
│   ├── 01-contract-first-design.md
│   └── 02-partial-credit-scoring.md
└── snippets/            # 匿名の技術デモ用サンプル / anonymized illustrative samples
    ├── question.proto
    └── partial_credit_scorer.py
```

## Feature deep-dives / 各機能の詳細

| # | Feature / 機能 | 見どころ / Highlights |
| --- | --- | --- |
| 01 | [Contract-First Design / コントラクトファースト設計](features/01-contract-first-design.md) | OpenAPI＋Protobufで契約を先に定義・並行開発・型整合 |
| 02 | [Partial-Credit Scoring / 部分点採点モデル](features/02-partial-credit-scoring.md) | 設問ツリー・加点グループ（排他）・減点・クランプの型設計 |

## Disclaimer / ディスクレーマー

All identifiers, field names, and values shown anywhere in this repository are **placeholders or generic examples**. The snippets are simplified illustrations authored for this portfolio and are **not** the production source. No company, customer, or personal information is included.

本リポジトリ内の識別子・フィールド名・値はすべて**プレースホルダまたは一般的な例**です。掲載コードはポートフォリオ用に簡略化して書き起こしたものであり、実運用ソースではありません。特定の企業・顧客・個人情報は一切含みません。
