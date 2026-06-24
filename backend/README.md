# Property Sale Screening - Backend (FastAPI)

FastAPI + PostgreSQL による REST API サーバー

## セットアップ

```bash
# 依存パッケージインストール
uv sync

# 環境変数設定
cp .env.example .env
# .env を編集して DATABASE_URL, SECRET_KEY などを設定

# 開発サーバー起動
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API ドキュメント

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/v1/health

## ディレクトリ構造

```
app/
├── api/v1/endpoints/   # ルーター・エンドポイント定義
├── api/v1/schemas/     # Pydantic Request/Response モデル
├── core/               # 設定・依存注入・セキュリティ
├── models/             # SQLAlchemy ORM モデル
├── services/           # ビジネスロジック
├── repositories/       # データアクセス層
└── middleware/         # カスタムミドルウェア
```

## 認証方式

JWT + HttpOnly Cookie（XSS 対策・CSRF 対策必要）

## OpenAPI スキーマ出力（Slice 0-6 用）

```bash
uv run python scripts/export_openapi.py -o openapi.json
```
