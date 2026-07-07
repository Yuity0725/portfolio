# Tech Stack / 技術スタック

The stack used across the platform. Versions reflect the majors used in the project.
プラットフォーム全体で使用した技術一覧。バージョンはプロジェクトで用いたメジャー系を記載。

## Frontend / フロントエンド

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Next.js (App Router) | 14 | ユーザー向けUI / SSR・ルーティング |
| React | 18+ | UIコンポーネント |
| TypeScript | 5.x | 型安全なフロント実装 |
| NextAuth.js | — | 認証（Google / Microsoft OAuth） |
| Prisma | 5.x | ORM（型付きDBアクセス） |
| Vercel | — | ホスティング / デプロイ |

## Backend — Python / バックエンド（Python）

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| FastAPI | 0.115+ | REST API（複数のLambda関数） |
| Pydantic | 2.x | 構造化データ・バリデーション（`Any`排除） |
| Uvicorn | 0.32 | ASGIサーバ（ローカル実行） |
| Mangum | 0.20 | ASGI → Lambda アダプタ |
| Lambda Web Adapter | — | FastAPIをLambdaで直接実行 |

## Backend — Node.js / バックエンド（Node.js）

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Node.js | 20.x | Deep Research バックエンド実行環境 |
| Express | 4.x | HTTPサーバ |
| Mastra | 0.23 | マルチエージェント・ワークフロー |
| @ai-sdk/google, @ai-sdk/openai | — | LLMクライアント |
| Zod | 3.x | バリデーション |
| Prisma | 5.x | ORM |
| Exa (exa-js) | 1.8 | Web検索 |

## Data & Search / データ・検索

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| TiDB Cloud | — | メインDB（MySQL互換・クラウド） |
| Amazon OpenSearch | 3.x (client) | 全文検索（4インデックス, VPC内） |
| Sudachi / GiNZA | 5.2 | 日本語形態素解析・ユーザー辞書 |
| SQLAlchemy | 2.0 | Python ORM / クエリ |
| tidb_vector | 0.0.15 | ベクトル検索 |

## AI / NLP

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Google Gemini (google-genai) | 1.x | RAG応答・Deep Researchのレポート生成 |
| transformers | 4.54 | 埋め込み・分類 |
| spaCy + GiNZA | 3.8 / 5.2 | 日本語NLP処理 |

## Infrastructure (AWS) / インフラ

| Technology | Purpose / 用途 |
| --- | --- |
| AWS Lambda (arm64) | サーバーレスAPI実行 |
| API Gateway (REST / HTTP) | APIエンドポイント・レスポンスストリーミング |
| ECS Fargate | バッチ処理（マイグレーション） |
| Step Functions | バッチの直列オーケストレーション |
| EventBridge Scheduler | 定期実行（weekly cron） |
| S3 | 辞書ファイル・ビルド成果物・Terraform state |
| ECR | コンテナイメージレジストリ |
| SSM Parameter Store / Secrets Manager | 機密情報管理 |
| Terraform (>= 1.0, AWS Provider 4–6) | Infrastructure as Code |

## Observability & Ops / 監視・運用

| Technology | Purpose / 用途 |
| --- | --- |
| Logfire | 集約ログ（Pydantic製・OTel対応） |
| OpenTelemetry | トレース・メトリクスのエクスポート |
| CloudWatch Logs | Lambda / Fargate ログ |
| AWS X-Ray | 分散トレーシング |

## CI/CD & Dev / CI/CD・開発

| Technology | Purpose / 用途 |
| --- | --- |
| GitHub Actions | CI/CD（OIDC → ECR push → Lambda更新 → スモークテスト） |
| DevContainer (VS Code) | 開発環境の標準化 |
| pytest / Jest | テスト（Python / Node.js） |
| ESLint / Prettier / tsc | Lint・整形・型チェック |
