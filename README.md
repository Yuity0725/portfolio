# Portfolio / ポートフォリオ

> エンジニアとしての制作物・技術ケーススタディをまとめたリポジトリです。
> A collection of engineering work and technical case studies.
>
> 各プロジェクトは独立したサブディレクトリとして格納され、**今後も継続的に追加**されていきます。
> Each project lives in its own self-contained subdirectory, and **new projects are added over time**.

---

## Projects / プロジェクト一覧

| # | Project / プロジェクト | 概要 / Summary | 主な技術 / Stack |
| --- | --- | --- | --- |
| 01 | [civic-document-ai-platform](civic-document-ai-platform/) 📄 | 日本の行政公開文書をAIで横断検索・要約・深掘り分析する基盤 / AI cross-search, RAG chat & deep-research for Japanese public-sector documents | Next.js・FastAPI・Mastra・AWS Serverless・OpenSearch(Sudachi)・TiDB・Gemini・Terraform |
| 02 | [local-llm-inference-platform](local-llm-inference-platform/) | NVIDIA DGX Spark 2ノード上のオンプレLLM推論基盤の設計・構築・運用 / Design & operation of an on-prem LLM inference platform on a 2-node NVIDIA DGX Spark cluster | SGLang・llama.cpp・vLLM・Ray・nginx・CUDA 13 (ARM64/`sm_121`)・GGUF/FP8・Pydantic |
| 03 | [math_optimizer_agent](math_optimizer_agent/) | LLMが自然言語の依頼から数理最適化アルゴリズムを選び、製造工程DAGを最適化するエージェントのデモ / LLM agent that picks a math-optimization algorithm from a natural-language request and optimizes a manufacturing-process DAG | Python・Streamlit・pydantic-ai・NetworkX・OpenAI |
| 04 | [grading-ops-platform](grading-ops-platform/) 📄 | 教育企業の答案添削オペレーションを支えるフルスタック業務基盤（Next.jsフロント＋Django REST＋Go/Python非同期サービスをCognito SSOで統合）/ Full-stack ops platform for an education company's answer-sheet grading business — one SSO identity across a frontend and two backends | Next.js・TypeScript・Django REST・Go・ECS・SQS・Lambda・Step Functions・Terraform |
| 05 | [modular-monolith-api](modular-monolith-api/) 📄 | 教育企業の社内APIプラットフォーム（FastAPIモジュラーモノリス／クリーンアーキテクチャ・DDD）/ An education company's internal API platform — a FastAPI modular monolith with clean/DDD layering | FastAPI・Python・Pydantic・SQLAlchemy・PostgreSQL・Docker・ECS |

📄 = 匿名化ケーススタディ（実ソース非掲載・手書き匿名スニペット）/ anonymized case study — no proprietary source, hand-authored snippets. マークなしは実ソース公開 / unmarked = real source published.

<!--
新しいプロジェクトを追加したら、上の表に1行足してください。
When you add a new project, append a row to the table above.
-->



---

## Structure / 構成

```
portfolio/
├── README.md                     # 本書：ポートフォリオの入口 / this file — portfolio index
├── .gitignore
└── <project-name>/               # プロジェクトごとに1ディレクトリ / one directory per project
    ├── README.md                 # そのプロジェクトの説明 / project overview
    └── ...
```

各プロジェクトは自己完結しており、それぞれの `README.md` から詳細（アーキテクチャ・技術スタック・機能解説など）をたどれます。
Each project is self-contained; start from its own `README.md` to explore architecture, tech stack, and feature deep-dives.

### 新しいプロジェクトの追加 / Adding a new project

1. `portfolio/<project-name>/` を作成し、コードやドキュメントを配置 / create the directory and add its files
2. 各プロジェクト直下に `README.md` を用意 / add a project-level `README.md`
3. 上の **Projects** 表に1行追加 / append a row to the **Projects** table above

---

## Note / 注記

一部のプロジェクトは商用IP・認証情報の保護のため、実プロダクトのソースをそのまま掲載せず、**アーキテクチャ解説と匿名化した技術サンプル**で構成した**ポートフォリオ用ケーススタディ**として公開しています。詳細は各プロジェクトの `README.md` を参照してください。

Some projects are published as **portfolio case studies** — to protect commercial IP and credentials, they contain architecture write-ups and **hand-authored, anonymized snippets** rather than proprietary production source. See each project's `README.md` for details.
