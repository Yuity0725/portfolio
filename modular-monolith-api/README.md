# Internal Operations API Platform

> A modular-monolith internal API platform (FastAPI / Python) for an education company's back-office operations — staff SSO sessions, an answer-grading master database, capacity & assignment optimization, and Slack / legacy-system integrations — built with clean-architecture (DDD) layering.
>
> 教育系企業の社内業務を支える、モジュラーモノリス構成の内部APIプラットフォーム（FastAPI / Python）。スタッフSSOセッション、答案添削のマスタDB、可能工数・割当最適化、Slack／レガシー基幹システム連携などを、クリーンアーキテクチャ（DDD）のレイヤリングで実装。

> **Note / 注記**
> This is a **portfolio case study**. To protect commercial IP and credentials, no proprietary source code is published here — the repository contains architecture write-ups and **hand-authored, anonymized snippets** that illustrate the engineering.
> これは**ポートフォリオ用のケーススタディ**です。商用IPと認証情報保護のため実プロダクトのソースは掲載していません。掲載コードはすべて**技術デモ用に書き起こした匿名サンプル**です。

---

## English (Summary)

An internal platform that consolidates a back-office operations team's tools behind one Python API. Rather than fragmenting the system into many microservices, it is deliberately a **modular monolith**: a single FastAPI deployable partitioned into independent **bounded contexts** (staff session/SSO, grading master data, grader capacity, assignment optimization, Slack integration, legacy-system integration, org master data), each internally structured with **clean-architecture / DDD layering** and **dependency inversion**.

Every context follows the same shape — `domains` (entities, value objects, repositories, interfaces) ← `applications` (usecases) → `adapters` (controllers, DB gateways) → `infrastructures` (FastAPI routers). Domain logic depends only on abstract interfaces; concrete SQLAlchemy / external-API implementations are injected at a per-context composition root. The result is microservice-like modularity and testability with monolith-like operational simplicity.

Engineered end-to-end: domain modeling, the layered application code, the PostgreSQL data layer with Alembic migrations, container packaging, and the AWS ECS (Fargate) deployment pipeline.

**Highlights**
- **Modular monolith** — one FastAPI app, ~10 bounded contexts, each independently layered; routers composed in a single `main.py`.
- **Clean architecture / DDD** — dependency inversion via abstract DB-gateway interfaces in the domain; Repository / Specification / Builder / Facade / Adapter patterns.
- **Staff SSO** — Cognito JWT (RS256, JWKS) verification middleware that mints short-lived session cookies.
- **Optimization** — a linear-programming (PuLP) assignment engine that maximizes preference under capacity constraints, run asynchronously via a container Lambda + SQS FIFO.
- **Integrations** — a typed Slack façade (post / channel / invite / upload) and an anti-corruption façade over a legacy operations console.
- **Type safety & tests** — Pydantic at the API boundary, `mypy` / `flake8` in CI, and `pytest` unit tests that swap in in-memory fake gateways thanks to the interface seams.

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for diagrams and **[TECH_STACK.md](TECH_STACK.md)** for the full stack.

---

## 日本語（詳細）

### これは何か

社内の業務チームが使う複数のツール（スタッフ認証、答案添削のマスタ管理、添削者の可能工数管理、答案と添削者の割当最適化、Slack連携、レガシー基幹システム連携、組織マスタ）を、**1つのPython API**の裏側に集約した内部プラットフォームです。

システムを多数のマイクロサービスに分割するのではなく、意図的に **モジュラーモノリス** として構築しています。単一のFastAPIデプロイ単位を、独立した **境界づけられたコンテキスト（bounded context）** に分割し、各コンテキストの内部を **クリーンアーキテクチャ / DDD のレイヤリング** と **依存性逆転** で構成しています。

### 解決した課題 → アプローチ

| 課題 | アプローチ |
| --- | --- |
| 複数の業務ツールが乱立し、認証・DB・デプロイがばらばら | **モジュラーモノリス**で単一デプロイに集約。境界づけられたコンテキストで内部を疎結合化（→ [features/01](features/01-modular-monolith.md)） |
| ドメインロジックがDBやフレームワークに密結合しがち | **クリーンアーキテクチャ／DDD**。ドメインに抽象インターフェースを置き、実装（SQLAlchemy・外部API）を`adapters`に隔離（依存性逆転）（→ [features/02](features/02-clean-architecture-ddd.md)） |
| 社内スタッフの認証を安全に共通化したい | Cognito発行のJWT（RS256／JWKS）を検証するミドルウェアで短命なセッションCookieを発行 |
| 答案と添削者の割当を人手で最適化するのは限界 | **線形計画法（PuLP）** で選好を最大化しつつ可能工数制約を満たす割当を計算。SQS＋コンテナLambdaで非同期実行 |
| 型崩れ・リグレッションを継続的に防ぎたい | 境界でPydantic検証、CIで`mypy`/`flake8`、インターフェースの継ぎ目を使ったフェイク差し替えで`pytest`ユニットテスト（→ [features/03](features/03-type-safety-and-testing.md)） |
| 既存の運用（Slack・レガシー基幹）と接続したい | 型付きSlackファサードと、レガシー基幹への腐敗防止ファサードを内部APIとして提供（→ [features/04](features/04-operations-integration.md)） |

### 主要機能

1. **スタッフSSO／セッション** — Cognito JWTを検証し、セッションCookieを発行・更新するミドルウェア
2. **答案・添削マスタDB** — 試験種・答案ログ・工数テーブルのCRUDと集計
3. **可能工数管理** — 添削者ごと・日付ごとの処理可能工数（capacity）の登録と期間集計
4. **割当最適化** — 答案（依頼）と添削者を、選好最大・工数制約下で割り当てる線形計画エンジン（非同期）
5. **Slack連携** — チャンネル作成・招待・テキスト／リッチテキスト投稿・ファイルアップロードの型付きファサード
6. **レガシー基幹連携** — 外部の運用コンソールに対する腐敗防止ファサード（受領答案検索・添削者変更・返却 等）
7. **組織マスタ** — 従業員・チーム・業務セグメントのマスタ管理

### 技術的な工夫（抜粋）

- **モジュラーモノリス＋境界づけられたコンテキスト** — マイクロサービス化の運用コストを避けつつ、コンテキスト単位で疎結合・独立進化できる構造を選択 → [features/01](features/01-modular-monolith.md)
- **依存性逆転（DIP）** — `domains/interfaces` に抽象DBゲートウェイを定義し、`adapters/db_gateways` の SQLAlchemy 実装を注入。ドメインはフレームワークを知らない → [snippets/repository_and_gateway.py](snippets/repository_and_gateway.py)
- **DDD の戦術パターン** — Entity / Value Object、Repository、Specification、Builder、Facade、DTO⇄Entity マッパー（`from_entity`/`to_entity`）を用途に応じて使い分け → [snippets/domain_models.py](snippets/domain_models.py)
- **境界の型安全** — API境界のリクエスト／レスポンスは Pydantic `BaseModel`＋`Field` で定義し、ドメインの `dataclass` へ変換 → [snippets/router_and_controller.py](snippets/router_and_controller.py)
- **テスト容易性** — インターフェースの継ぎ目にインメモリのフェイクゲートウェイを差し込み、DBなしでユースケースを単体テスト → [features/03](features/03-type-safety-and-testing.md)
- **合成ルート（composition root）** — 各コンテキストの `__init__.py` で ゲートウェイ→ユースケース→コントローラ→ルーター を結線し、`main.py` が全ルーターを束ねる → [snippets/application_usecase.py](snippets/application_usecase.py)

### 担当領域

設計〜実装〜インフラまでを一気通貫で担当（ドメインモデリング、レイヤードなアプリケーション実装、PostgreSQL＋Alembicのデータ層、Dockerによるコンテナ化、AWS ECS(Fargate) へのデプロイパイプライン）。

---

## Feature deep-dives / 各機能の詳細

機能・設計トピックごとに技術的な工夫点をまとめた個別ドキュメントを用意しています（→ [features/](features/README.md)）。

| # | Topic / トピック | 見どころ / Highlights |
| --- | --- | --- |
| 01 | [Modular Monolith / モジュラーモノリス構成](features/01-modular-monolith.md) | 境界づけられたコンテキスト・単一デプロイ・なぜマイクロサービスにしないか |
| 02 | [Clean Architecture & DDD / クリーンアーキテクチャとDDD](features/02-clean-architecture-ddd.md) | domain/usecase/adapter・依存性逆転・Repository/Specification/Builder |
| 03 | [Type Safety & Testing / 型安全とテスト戦略](features/03-type-safety-and-testing.md) | Pydantic境界・mypy/flake8・フェイク差し替えのユニット/インテグレーション |
| 04 | [Operations Integration / 運用連携](features/04-operations-integration.md) | Slackファサード・レガシー腐敗防止層・LP割当の内部API |

## Repository layout / このリポジトリの構成

```
modular-monolith-api/
├── README.md            # 本書 / this file
├── ARCHITECTURE.md      # 構成図（Mermaid）と設計判断 / diagrams & design decisions
├── TECH_STACK.md        # 技術スタック一覧 / full tech stack table
├── features/            # 各トピックの工夫点（個別ドキュメント）/ per-topic deep-dives
│   ├── 01-modular-monolith.md
│   ├── 02-clean-architecture-ddd.md
│   ├── 03-type-safety-and-testing.md
│   └── 04-operations-integration.md
└── snippets/            # 匿名の技術デモ用サンプル / anonymized illustrative samples
    ├── domain_models.py             # ドメインの Value Object / Entity
    ├── repository_and_gateway.py    # 抽象インターフェース + SQLAlchemy 実装
    ├── router_and_controller.py     # FastAPI ルーター + Pydantic コントローラ
    └── application_usecase.py       # ユースケース + 合成ルート
```

## Disclaimer / ディスクレーマー

All identifiers (account IDs, endpoints, hostnames, ARNs, resource names, keys) shown anywhere in this repository are **placeholders**. The employer, product names, and business specifics are intentionally generalized. The snippets are simplified illustrations authored for this portfolio and are **not** the production source.

本リポジトリ内の識別子（アカウントID・エンドポイント・ホスト名・ARN・リソース名・キー等）はすべて**プレースホルダ**です。所属企業・製品名・事業の詳細は意図的に一般化しています。掲載コードはポートフォリオ用に簡略化して書き起こしたものであり、実運用ソースではありません。
