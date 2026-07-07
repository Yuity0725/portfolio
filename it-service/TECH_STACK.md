# Tech Stack / 技術スタック

The stack used across the platform. Versions reflect those pinned in the project's dependency manifests (they are not secrets).
プラットフォーム全体で使用した技術一覧。バージョンはプロジェクトの依存定義に固定されていた値を記載（秘匿情報ではありません）。

## Backend — Core / バックエンド（コア）

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Python | 3.9 | 実装言語 |
| FastAPI | 0.75 | REST API フレームワーク（ルーター／DI／OpenAPI） |
| Starlette | 0.17 | ASGI 基盤・ミドルウェア（セッション認証） |
| Pydantic | 1.9 | API境界のスキーマ・バリデーション |
| Uvicorn | 0.17 | ASGI サーバ（コンテナで起動） |
| PyJWT | 2.4 | Cognito JWT（RS256）検証 |
| cryptography | 37.x | JWK → 公開鍵の変換（RSAアルゴリズム） |

## Domain & Application / ドメイン・アプリケーション

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| dataclasses (標準) | — | Entity / Value Object（`frozen=True`）の表現 |
| abc (標準) | — | ドメインの抽象インターフェース（依存性逆転） |
| PuLP | 2.6 | 線形計画法による割当最適化（CBCソルバ） |
| slack-sdk | 3.16 | Slack Web API クライアント（ファサードで隠蔽） |
| beautifulsoup4 / html5lib | 4.11 / 1.1 | レガシー運用コンソール連携時のHTMLパース |

## Data & Persistence / データ・永続化

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| PostgreSQL | 13.1 | メインDB（本番／ローカルとも） |
| SQLAlchemy | 1.4 | ORM・クエリ（`adapters/db_gateways` に隔離） |
| Alembic | 1.5 | DBマイグレーション（autogenerate） |
| psycopg2-binary | 2.9 | PostgreSQL ドライバ（同期） |
| asyncpg | 0.26 | PostgreSQL ドライバ（非同期） |
| databases | 0.4 | 非同期DBアクセス補助 |

## Infrastructure (AWS) / インフラ

| Technology | Purpose / 用途 |
| --- | --- |
| ECS (Fargate) | FastAPIコンテナの常駐実行（`taskdef.json`） |
| Application Load Balancer | HTTP(S) 受け口・ヘルスチェック |
| ECR | コンテナイメージレジストリ |
| CodeBuild | イメージビルド・push（`buildspec.yaml`） |
| CodeDeploy | ECS の blue/green デプロイ（`appspec.yaml`） |
| Amazon Cognito | スタッフSSO（JWT発行・JWKS公開） |
| SQS (FIFO) | 割当最適化ジョブの非同期キュー |
| AWS Lambda (container image) | 線形計画ソルバの実行環境 |
| Secrets Manager | DB認証情報等の秘匿値（起動時に注入） |
| CloudWatch Logs | コンテナログ集約（`awslogs` ドライバ） |
| IAM | タスク実行ロール・最小権限 |

## Dev, Build & CI/CD / 開発・ビルド・CI/CD

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Docker / Docker Compose | — | コンテナ化・ローカル開発（server + db） |
| boto3 / botocore | 1.24 / 1.27 | AWS SDK（SQS 等） |
| pytest | 7.1 | ユニット／E2E テスト |
| mypy | — | 静的型チェック（`ignore_missing_imports`） |
| flake8 | — | Lint（`max-line-length=120`, migrations 除外） |
| isort | 5.10 | import 整列 |
| GitHub Actions | — | CI（`pytest` と `flake8` を PR/push で実行） |

## Patterns & Practices / 設計パターン・プラクティス

| Practice | Purpose / 用途 |
| --- | --- |
| Modular Monolith / Bounded Context | 単一デプロイ内でドメインを疎結合に分割 |
| Clean Architecture / DDD 層分割 | domain / application / adapter / infrastructure |
| Dependency Inversion | ドメインの抽象インターフェースに実装を注入 |
| Repository / Specification / Builder | 永続化・検索条件・生成ロジックの分離 |
| Facade / Anti-Corruption Layer | Slack SDK・レガシー基幹を型付きファサードで隠蔽 |
| DTO ⇄ Entity マッパー | `from_entity` / `to_entity` で ORM とドメインを分離 |
| Composition Root | 各コンテキストの `__init__.py` で依存を結線 |
