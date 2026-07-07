# Tech Stack / 技術スタック

The technologies used to define and model the contract-first specification.
契約ファースト仕様の定義・モデリングに用いた技術一覧。

## Contract / Schema — 契約・スキーマ定義

| Category / 分類 | Technology | Purpose / 用途 |
| --- | --- | --- |
| REST API contract | OpenAPI 3.0 | エンドポイント・リクエスト/レスポンス・スキーマをAPI契約として先に定義 |
| Data / message schema | Protocol Buffers | 設問・採点基準・座標を言語非依存の型付きメッセージとして定義 |
| Enumerations | OpenAPI `enum` / Protobuf `enum` | 設問形式（選択式/短答式/自由記述/回答不可）を固定し曖昧さを排除 |

## Domain Model — ドメインモデル（採点ロジック）

| Category / 分類 | Technology | Purpose / 用途 |
| --- | --- | --- |
| Language | Python 3.x | 採点ドメインモデル・部分点ロジックの実装 |
| Value objects | `dataclasses` (`frozen=True`) | 不変な値オブジェクトで採点モデルを表現（副作用の少ない設計） |
| Type hints | `typing` (`Optional`, `list`, `tuple`, `frozenset`) | 設問ツリー・加点/減点・位置情報の型を明示 |
| Enumerations | `enum.Enum` | 設問形式を型安全な列挙で表現 |

## Quality / Tooling — 品質・ツール

| Category / 分類 | Technology | Purpose / 用途 |
| --- | --- | --- |
| Static type check | mypy | ドメインモデルの静的型チェックで契約とコードの乖離を防止 |
| Version control | Git | 契約変更のレビュー・破壊的変更の検知 |

## Referenced infrastructure — 契約が前提とする周辺構成（generic）

| Category / 分類 | Technology | Purpose / 用途 |
| --- | --- | --- |
| Answer-sheet storage | Object storage + presigned URL | 答案PDF/画像を署名付きURLで受け渡し（識別子はプレースホルダ） |
| Authentication | OIDC / Bearer + HttpOnly session cookie | マネージドIdPのOIDCトークンで認証し、セッションはHttpOnly Cookieで保持 |

> Versions reflect the majors used. All hostnames, IDs, and endpoints referenced by the contract are placeholders.
> バージョンは使用したメジャー系を記載。契約が参照するホスト名・ID・エンドポイントはすべてプレースホルダ。
