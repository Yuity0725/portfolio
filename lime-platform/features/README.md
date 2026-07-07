# Feature Deep-Dives / 各機能の詳細

Per-feature write-ups focusing on the engineering decisions and their rationale.
機能ごとに、技術的な工夫点と「なぜそうしたか」を掘り下げたドキュメント群。

| # | Feature / 機能 | What it shows / 見どころ |
| --- | --- | --- |
| 01 | [Full-Stack & Cognito SSO Auth / フルスタック構成とSSO認証](01-fullstack-sso-auth.md) | 単一ユーザープール・各サービス独立検証・カスタムクレーム由来のスタッフID・JWKSキャッシュ |
| 02 | [Async Offload (SQS→Lambda) / 重い処理の非同期化](02-async-offload-sqs-lambda.md) | ECS上のDRF API・FIFO SQS投入・`worker`ディスパッチのLambda・OpenCV画像処理 |
| 03 | [ADPAL Async Search & Return / 非同期答案検索・返却](03-adpal-async-search-return.md) | Goゲートウェイ（clean architecture）・AWS Batch・DynamoDBジョブ管理・カーソルページング |
| 04 | [Auto-Return Pipeline / 自動返却パイプライン](04-auto-return-pipeline.md) | Step FunctionsのMap並列・Wait/Choiceポーリング・Retry/Catch・EventBridge定期起動 |
| 05 | [Frontend Architecture / フロントエンド設計](05-frontend-architecture.md) | Atomic Design・Storybook・型付きAPI層・環境別設定・AES暗号化ストレージ |
| 06 | [IaC & CI/CD / インフラと継続デリバリ](06-iac-cicd.md) | Terraformモジュール＋環境別スタック・GitHub Actions/CodeBuild・マルチアカウントECR |

> 全体像は [../README.md](../README.md)、構成図は [../ARCHITECTURE.md](../ARCHITECTURE.md)、技術一覧は [../TECH_STACK.md](../TECH_STACK.md) を参照。
