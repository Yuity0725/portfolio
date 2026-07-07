# Grading Operations Platform

> A full-stack internal operations platform for an education / e-learning company's answer-sheet grading (答案添削) business — one Next.js frontend and two backends (a Django REST API and a set of Go/Python async services) unified by a single Cognito SSO identity.
>
> ある教育・eラーニング企業の社内業務および答案添削オペレーションを支える、フルスタックの業務基盤。1つのNext.jsフロントエンドと2つのバックエンド（Django REST APIと、Go/Pythonの非同期サービス群）を、共通のCognito SSO IDで束ねている。

> **Note / 注記**
> This is a **portfolio case study**. To protect commercial IP and credentials, no proprietary source code is published here — the repository contains architecture write-ups and **hand-authored, anonymized snippets** that illustrate the engineering.
> これは**ポートフォリオ用のケーススタディ**です。商用IPと認証情報保護のため実プロダクトのソースは掲載していません。掲載コードはすべて**技術デモ用に書き起こした匿名サンプル**です。

---

## English (Summary)

A production platform that runs the day-to-day operations of an answer-sheet grading business: staff search for answer sheets, (re)assign examiners, run bulk confirmations, and return graded sheets — much of which is **heavy, long-running work** that cannot block a web request.

The system is deliberately split into **three deployables** that share one identity:

- **Frontend** — a Next.js / TypeScript SPA (Atomic Design, Storybook) for staff, authenticated with Cognito via AWS Amplify.
- **Main API** — a Django REST Framework service on **ECS Fargate**. It owns the business data and offloads heavy jobs (answer-sheet image processing, bulk operations) to **SQS → Lambda** workers.
- **ADPAL & auto-return** — Go API gateways + Python batch workers for **asynchronous answer-sheet search & return**, with a long-running **auto-return pipeline** orchestrated by **AWS Step Functions + EventBridge**, all provisioned with **Terraform** across multiple environments.

Engineered end-to-end by a single engineer: frontend, both backends (Python & Go), the async pipelines, and the Infrastructure-as-Code.

**Highlights**
- **Full-stack, multi-language** — Next.js/TypeScript frontend, Django/DRF (Python) main API, Go gateways + Python batch workers.
- **One SSO identity across every service** — a Cognito JWT (ID token) verified independently by the frontend, the Django API, and the Go gateways; a staff/examiner identity is derived from a custom claim.
- **Async-first** — SQS→Lambda for image-heavy work, **AWS Batch** for long search/return jobs, **Step Functions** (Map fan-out + poll + retry) for the auto-return pipeline.
- **Event-driven orchestration** — EventBridge Scheduler drives the state machine; every task has bounded retries, backoff, and a dedicated error path.
- **Typed everywhere** — TypeScript on the front, DRF serializers + typed workers on the Django side, OpenAPI-generated types on the Go gateways.
- **IaC + CI/CD** — Terraform modules with per-environment stacks, GitHub Actions + CodeBuild/CodeDeploy, and multi-account ECR.

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for diagrams and **[TECH_STACK.md](TECH_STACK.md)** for the full stack.

---

## 日本語（詳細）

### これは何か

答案添削（答案用紙の採点・返却）業務を回すための社内業務基盤です。スタッフは答案を検索し、添削者の割り当て変更や一括確定を行い、採点済み答案を返却します。これらの多くは**重く時間のかかる処理**で、Webリクエストの中で同期的に完結させられません。

そこで本システムは、**1つのIDで束ねた3つのデプロイ対象**に意図的に分割しています。

- **フロントエンド** — スタッフ向けのNext.js / TypeScript製SPA（Atomic Design・Storybook）。AWS Amplify経由でCognito認証。
- **メインAPI** — **ECS Fargate**上で動くDjango REST Framework。業務データを保持し、重い処理（答案画像処理・一括操作）を**SQS → Lambda**ワーカーへ委譲。
- **ADPAL・自動返却** — **非同期の答案検索・返却**を担うGo製APIゲートウェイ＋Pythonバッチワーカー。長時間の**自動返却パイプライン**を**AWS Step Functions + EventBridge**でオーケストレーションし、全体を**Terraform**でマルチ環境にプロビジョニング。

### 解決した課題 → アプローチ

| 課題 | アプローチ |
| --- | --- |
| 3つのサービスにまたがってスタッフを一意に識別し、二重ログインを避けたい | **Cognito SSO**：単一ユーザープールのIDトークン（JWT）を各サービスが独立に検証。カスタムクレームからスタッフ/添削者IDを導出（[feature 01](features/01-fullstack-sso-auth.md)） |
| 答案の画像処理や一括確定など重い処理がWebリクエストを詰まらせる | **SQS → Lambda**へ処理を委譲。APIは即応、ワーカーがOpenCV/PDF処理を非同期実行（[feature 02](features/02-async-offload-sqs-lambda.md)） |
| 大量の答案検索・返却は数分〜数十分かかり、同期APIに載らない | **ADPAL**：Goゲートウェイが**AWS Batch**ジョブを投入し、状態と結果を**DynamoDB**で管理。クライアントはジョブIDでポーリング（[feature 03](features/03-adpal-async-search-return.md)） |
| 定期的な自動返却を、失敗しても止まらず・観測可能に回したい | **Step Functions**のMap並列＋ポーリング＋リトライ＋専用エラーパスで状態機械化し、**EventBridge**で定期起動（[feature 04](features/04-auto-return-pipeline.md)） |
| 業務UIを保守可能な形で作り、機密値を安全に扱いたい | **Atomic Design + Storybook + 型付きAPI層**、環境別設定、ローカルストレージの機密値はAES暗号化（[feature 05](features/05-frontend-architecture.md)） |
| 複数サービス・複数環境・複数アカウントを再現性高く運用したい | **Terraformモジュール + 環境別スタック**、GitHub Actions + CodeBuild/CodeDeploy、マルチアカウントECR（[feature 06](features/06-iac-cicd.md)） |

### 主要機能

1. **横断SSO認証** — 1つのCognitoユーザープールのIDトークンを、フロント・Django・Goゲートウェイが各々検証し、スタッフを一意に識別
2. **重い処理の非同期化** — メインAPIがSQSにメッセージ投入 → Lambdaワーカーが答案画像処理・一括確定を実行
3. **ADPAL 非同期検索・返却** — 検索/返却ジョブを投入し、AWS Batchで実行、DynamoDBで状態管理、ポーリングで取得
4. **自動返却パイプライン** — Step Functions state machineが検索→返却を直列・並列で自動実行し、EventBridgeで定期起動
5. **業務フロントエンド** — Atomic Designのコンポーネント群、Storybook、型付きAPIクライアント層、暗号化ストレージ
6. **IaC / CI/CD** — Terraformマルチ環境、GitHub Actions・CodeBuild/CodeDeploy、マルチアカウントECR

### 技術的な工夫（抜粋）

- **1トークン・全サービス横断のSSO** — Djangoはミドルウェアで、GoゲートウェイはHTTPミドルウェアで、同じCognito IDトークンを検証。JWKSはキャッシュして検証コストを抑える → [snippets/go_gateway_handler.go](snippets/go_gateway_handler.go)
- **即応 × 非同期実行** — 重い処理はFIFO SQSに投げ、`worker`キーでハンドラをディスパッチするLambdaが実行。イベントは型付きモデルで受ける → [snippets/sqs_lambda_worker.py](snippets/sqs_lambda_worker.py)
- **ジョブAPIパターン** — 「投入→ポーリング→結果取得」をDynamoDB（TTL付き）とAWS Batchで実現。長時間処理をHTTPから切り離す
- **観測可能なstate machine** — 各Taskに`Retry`（指数バックオフ）と`Catch`（エラー集約）を付与し、`Wait`＋`Choice`で最大リトライ上限まで状態をポーリング → [snippets/step_functions_module.tf](snippets/step_functions_module.tf)
- **型安全徹底** — DRFシリアライザで境界バリデーション、Goはoapi-codegenでOpenAPIから型生成、フロントはTypeScript → [snippets/drf_serializer.py](snippets/drf_serializer.py) / [snippets/typed_api_hook.tsx](snippets/typed_api_hook.tsx)

### 担当領域

設計〜実装〜インフラ〜運用までを一気通貫で担当（フロントエンド、Python/Goの複数バックエンド、SQS/Batch/Step Functionsの非同期基盤、Terraform IaC、CI/CD）。

---

## Feature deep-dives / 各機能の詳細

各機能ごとに技術的な工夫点をまとめた個別ドキュメントを用意しています（→ [features/](features/README.md)）。

| # | Feature / 機能 | 見どころ / Highlights |
| --- | --- | --- |
| 01 | [フルスタック構成とCognito SSO / Full-Stack & SSO Auth](features/01-fullstack-sso-auth.md) | 単一ユーザープール・各サービス独立検証・カスタムクレーム由来のスタッフID・JWKSキャッシュ |
| 02 | [重い処理の非同期化 / Async Offload](features/02-async-offload-sqs-lambda.md) | ECS上のDRF API・FIFO SQS投入・`worker`ディスパッチのLambda・画像処理 |
| 03 | [ADPAL 非同期検索・返却 / Async Search & Return](features/03-adpal-async-search-return.md) | Goゲートウェイ（clean architecture）・AWS Batch・DynamoDBジョブ管理・ポーリング |
| 04 | [自動返却パイプライン / Auto-Return Pipeline](features/04-auto-return-pipeline.md) | Step FunctionsのMap並列・Wait/Choiceポーリング・Retry/Catch・EventBridge定期起動 |
| 05 | [フロントエンド設計 / Frontend Architecture](features/05-frontend-architecture.md) | Atomic Design・Storybook・型付きAPI層・環境別設定・AES暗号化ストレージ |
| 06 | [IaC と CI/CD / IaC & CI-CD](features/06-iac-cicd.md) | Terraformモジュール＋環境別スタック・GitHub Actions/CodeBuild・マルチアカウントECR |

## Repository layout / このリポジトリの構成

```
grading-ops-platform/
├── README.md            # 本書 / this file
├── ARCHITECTURE.md      # 構成図（Mermaid）と設計判断 / diagrams & design decisions
├── TECH_STACK.md        # 技術スタック一覧 / full tech stack table
├── features/            # 各機能の工夫点（個別ドキュメント）/ per-feature deep-dives
│   ├── 01-fullstack-sso-auth.md
│   ├── 02-async-offload-sqs-lambda.md
│   ├── 03-adpal-async-search-return.md
│   ├── 04-auto-return-pipeline.md
│   ├── 05-frontend-architecture.md
│   └── 06-iac-cicd.md
└── snippets/            # 匿名の技術デモ用サンプル / anonymized illustrative samples
    ├── drf_serializer.py          # 型付きDRFシリアライザ＋バリデーション
    ├── sqs_lambda_worker.py       # SQS→Lambdaワーカー（型付きイベント）
    ├── step_functions_module.tf   # Step Functions state machineのTerraform骨子
    ├── go_gateway_handler.go      # Goゲートウェイのハンドラ＋認証ミドルウェア
    └── typed_api_hook.tsx         # 型付きReactデータフック＋環境変数設定
```

## Disclaimer / ディスクレーマー

The product is described **generically**: it serves an education / e-learning company's internal operations and answer-sheet grading business, and the employer is intentionally not named. All identifiers (account IDs, endpoints, hostnames, ARNs, pool/client IDs, keys) shown anywhere in this repository are **placeholders**. The snippets are simplified illustrations authored for this portfolio and are **not** the production source.

本プロダクトは**一般化**して記述しています（ある教育・eラーニング企業の社内業務および答案添削業務を対象とし、企業名は意図的に伏せています）。本リポジトリ内の識別子（アカウントID・エンドポイント・ホスト名・ARN・プール/クライアントID・キー等）はすべて**プレースホルダ**です。掲載コードはポートフォリオ用に簡略化して書き起こしたものであり、実運用ソースではありません。
