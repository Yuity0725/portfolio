# Tech Stack / 技術スタック

The stack used across the LIME Platform (1 frontend + 2 backends). Versions reflect the majors used in the project; they are drawn from the dependency manifests (`package.json`, `requirements.txt`, `go.mod`).
プラットフォーム全体（フロントエンド1 + バックエンド2）で使用した技術一覧。バージョンは各依存マニフェスト（`package.json` / `requirements.txt` / `go.mod`）で用いたメジャー系を記載。

---

## Frontend / フロントエンド

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Next.js | 13.5 | スタッフ向け業務UI（SSG/SSR・ルーティング・`next export`静的配信） |
| React | 18.2 | UIコンポーネント（Atomic Design） |
| TypeScript | 5.3 | 型安全なフロント実装 |
| AWS Amplify (aws-amplify / @aws-amplify/ui-react) | 6.0 / 6.1 | Cognito認証・IDトークン管理 |
| MUI (@mui/material, x-data-grid, x-tree-view) | 5.15 / 6 | UIコンポーネント・データグリッド |
| Recoil | 0.7 | クライアント状態管理 |
| React Hook Form | 7.49 | フォーム制御・バリデーション |
| axios | 1.6 | 型付きAPIクライアント層 |
| crypto-js | 4.2 | ローカルストレージの機密値をAES暗号化 |
| csv-parse / react-csv / encoding-japanese | 5.5 / 2.2 / 2.0 | CSV入出力（Shift_JIS対応） |
| mermaid / react-markdown / remark-gfm | 10.6 / 9.0 / 4.0 | ドキュメント・図の描画 |

## Frontend — Dev & Quality / 開発・品質

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Storybook | 7.6 | コンポーネントカタログ・UIの単体確認 |
| Jest / Testing Library | 29.7 / 14 | コンポーネント・ロジックのテスト |
| ESLint / Prettier | 8.57 / 3.2 | Lint・整形（simple-import-sort 等） |
| Husky / lint-staged | 8.0 / 13.3 | pre-commitでの自動Lint |
| Yarn (Berry) | 4.0.2 | パッケージ管理 |
| AWS Amplify Hosting | — | フロントのビルド・配信（`amplify.yml`） |

## Backend — Main API (Python) / メインAPI（Python）

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Django | 3.2 | Webフレームワーク（複数の業務「app」を集約） |
| Django REST Framework | 3.13 | REST API・シリアライザ・バリデーション |
| Celery + Redis (django-redis) | 5.2 / 5.0 | 非同期タスク・キャッシュ（JWKSキャッシュ等） |
| PyJWT / python-jose / cryptography | 2.1 / 3.3 / 3.4 | Cognito IDトークン（JWT）の署名検証 |
| drf-spectacular / drf-yasg | 0.23 / 1.21 | OpenAPIスキーマ生成 |
| django-filter / django-cors-headers / django-health-check | 21.1 / 3.8 / 3.16 | クエリフィルタ・CORS・ヘルスチェック |
| psycopg2-binary | 2.9 | PostgreSQL（RDS）ドライバ |
| boto3 / botocore | 1.20 | AWS SDK（SQS投入・S3等） |
| gunicorn | 20.1 | WSGIサーバ（ECS上で実行） |
| slack-sdk | 3.19 | Slack通知連携 |
| ruff / black / mypy / moto | — | Lint・整形・型チェック・AWSモックテスト |

## Backend — Async Workers (Python on Lambda) / 非同期ワーカー（Python / Lambda）

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| OpenCV (opencv-python / -contrib) | 4.6 | 答案画像の処理（位置合わせ・切り出し） |
| pdf2image / Pillow / numpy | 1.16 / 8.3 / 1.21 | PDF→画像変換・画像処理 |
| pyzbar | 0.1.8 | 答案上のバーコード/QR読み取り |
| PyJWT / cryptography | 2.1 / 3.4 | トークン検証 |
| requests | 2.26 | 内部POS APIへのアクセス |

## Backend — ADPAL / auto-return (Go & Python) / ADPAL・自動返却

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Go | 1.20 | 非同期ジョブAPIゲートウェイ・Step Functions用Lambda |
| aws-lambda-go / aws-lambda-go-api-proxy | 1.41 / 0.14 | Lambda上でchi HTTPサーバをAPI Gateway背後で実行 |
| chi (go-chi/chi) | 5.0 | HTTPルーター・ミドルウェア |
| oapi-codegen / kin-openapi | 1.13 / 0.118 | OpenAPI仕様からハンドラ/型を自動生成 |
| aws-sdk-go-v2 (dynamodb / batch) | 1.18 (ddb 1.20 / batch 1.23) | ジョブ状態のDynamoDB管理・AWS Batchジョブ投入 |
| go.uber.org/zap | 1.24 | 構造化ロギング |
| caarlos0/env | v7 | 環境変数からの設定ロード |
| robfig/cron | 1.2 | トリガー時刻のパース（自動返却） |
| golangci-lint / goimports | 1.52 | Lint・整形（tools as go modules） |
| Python (boto3 / beautifulsoup4 / requests) | 1.26 / 4.12 / 2.31 | ADPALバッチワーカー（内部POS API連携・レスポンス解析） |

## Async & Orchestration / 非同期・オーケストレーション

| Technology | Purpose / 用途 |
| --- | --- |
| Amazon SQS (FIFO) | メインAPI → Lambdaワーカーへ重い処理を委譲 |
| AWS Lambda | SQSコンシューマ（画像処理ワーカー）／ADPALゲートウェイ／Step Functionsタスク |
| AWS Batch | ADPALの答案検索・返却ジョブ（長時間バッチ）実行 |
| AWS Step Functions | 自動返却パイプラインのオーケストレーション（Map並列・ポーリング・リトライ） |
| Amazon EventBridge (Scheduler) | 自動返却state machineの定期起動 |
| Amazon DynamoDB | 非同期ジョブの状態・結果ストア（TTL付き） |

## Infrastructure (AWS) / インフラ

| Technology | Purpose / 用途 |
| --- | --- |
| Amazon ECS (Fargate) | メインDjango APIの実行（常時稼働サービス） |
| Amazon API Gateway | ADPAL/自動返却ゲートウェイの公開エンドポイント |
| Amazon Cognito | 全サービス共通のユーザープール（SSO・IDトークン発行） |
| Amazon RDS (PostgreSQL) | メインAPIの永続データ |
| Amazon ElastiCache / Redis | Celeryブローカ・キャッシュ |
| Amazon S3 | 成果物・ファイル・Terraform state |
| Amazon ECR | コンテナイメージレジストリ（マルチアカウント） |
| VPC / Subnet / Security Group / Route53 / ACM | ネットワーク・DNS・TLS証明書 |
| Terraform (>= 1.x) | Infrastructure as Code（module + 複数環境） |

## CI/CD & Dev / CI/CD・開発

| Technology | Purpose / 用途 |
| --- | --- |
| GitHub Actions | CI（Lint/テスト/型チェック）・デプロイのトリガ |
| AWS CodeBuild / CodeDeploy | ECSへのビルド・Blue/Greenデプロイ（`buildspec` / `appspec` / `taskdef`） |
| AWS Amplify (Hosting) | フロントエンドのビルド・配信 |
| Docker | 各サービスのコンテナ化（ECS / Lambda / Batch） |
| pytest / Jest / go test | テスト（Python / TypeScript / Go） |
