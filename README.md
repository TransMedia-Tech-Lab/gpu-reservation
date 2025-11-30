# GPU Reservation Backend

研究室のGPUリソースを可視化し、日時指定の予約を管理するためのバックエンドです。FastAPI + SQLModel + SQLite を使用し、uv で仮想環境と依存関係を管理します。Backend のコードとデータは `backend/` ディレクトリ配下に集約しています。
現在の前提ハードウェアは **RTX 5090 32GB を1台 (lab-node-1/GPU0)** のみです。

## 技術スタック
- アプリ: FastAPI, Pydantic Settings, SQLModel/SQLAlchemy
- データベース: SQLite (デフォルトで `backend/data/gpu_reservations.db`)
- ランタイム/ツール: Python 3.13, uv (パッケージ管理・仮想環境), uvicorn (開発サーバー)
- その他: CORS は設定値で制御、OpenAPI UI は `/docs` と `/redoc` で利用可能

## アーキテクチャ
- `backend/app/main.py`: FastAPI アプリ本体とミドルウェア設定。
- `backend/app/routes.py`: API ルータ。リソースのCRUD、予約作成/更新/削除、可用性チェックなどを提供。
- `backend/app/services.py`: ビジネスロジック。予約の重複チェック、タイムゾーン正規化、可用性計算。
- `backend/app/models.py`: SQLModel で定義したテーブル/スキーマ (GPU, Reservation と各種リクエスト/レスポンス)。
- `backend/app/database.py`: エンジン生成・セッション依存性・テーブル初期化。
- `backend/app/config.py`: 設定値。`timezone`、`cors_origins`、`database_url` などを `.env` から上書き可能。
- `backend/app/seed.py`: 簡易サンプルデータ投入スクリプト。
- `backend/main.py`: uvicorn を起動するためのシンプルなエントリーポイント。
- エンドポイントは `settings.api_prefix` (デフォルト `/api`) 配下に集約。時刻は ISO8601 で受け取り、指定が無い場合は `timezone` (デフォルト UTC) を補完した上で UTC に正規化して保存します。重複条件は `start < 既存.end` かつ `end > 既存.start` を満たす予約をブロックします。

### データモデル概要
- GPU: `id`, `name`, `hostname`, `slot`, `model`, `memory_gb`, `notes`, `created_at`
- Reservation: `id`, `gpu_id`, `user`, `purpose`, `start_time`, `end_time`, `status`, `created_at`

## セットアップ
1. 前提: uv がインストールされていること。`cd /Users/yuhei/Desktop/Develop/gpu-reservation_2`
2. 依存関係と仮想環境の同期: `uv sync`
3. 開発サーバー起動:
   - ホットリロード付き: `uv run uvicorn backend.app.main:app --reload --port 8000`
   - 簡易エントリーポイント: `uv run python -m backend.main`
4. サンプルデータ投入 (任意): `uv run python -m backend.app.seed`
5. ブラウザで確認: `http://localhost:8000/docs` (Swagger UI) または `http://localhost:8000/redoc`

### 設定の変更
- `.env` に `DATABASE_URL`、`TIMEZONE`、`CORS_ORIGINS` (カンマ区切り) などを入れると上書きされます。
- デフォルトDBは SQLite ですが、`database_url` を他のRDBMSに差し替えれば対応可能です。

## API の使い方
- ベースURL: `http://localhost:8000/api`
- 主なエンドポイント:
  - `GET /health` ヘルスチェック
  - `POST /gpus` GPU登録
  - `GET /gpus` GPU一覧 + 現在の空き/次の予約
  - `GET /gpus/{gpu_id}` 特定GPUの現在ステータス
  - `PATCH /gpus/{gpu_id}` GPU情報更新
  - `GET /gpus/{gpu_id}/reservations?start&end` 時間条件付きで予約一覧
  - `GET /reservations?start&end&gpu_id` 全体またはGPU指定の予約一覧
  - `POST /reservations` 予約作成 (重複時は 409)
  - `PATCH /reservations/{reservation_id}` 予約時間・目的・ステータス更新 (重複チェックあり)
  - `DELETE /reservations/{reservation_id}` 予約削除
  - `GET /availability?start&end` 指定区間で利用可能/占有中GPUを返却

### 時刻指定の注意
- 例: `2025-01-20T13:00:00+09:00` のようにタイムゾーン付きで送るのが推奨。
- タイムゾーン無しの時刻は設定値 `timezone` (デフォルト UTC) とみなされ、DBにはUTCで保存されます。

### リクエスト例
```bash
# GPU 登録
curl -X POST http://localhost:8000/api/gpus \
  -H "Content-Type: application/json" \
  -d '{"name":"RTX5090-1","hostname":"lab-node-1","slot":"GPU0","model":"RTX 5090","memory_gb":32}'

# 予約作成
curl -X POST http://localhost:8000/api/reservations \
  -H "Content-Type: application/json" \
  -d '{"gpu_id":1,"user":"alice","purpose":"実験","start_time":"2025-01-20T13:00:00+09:00","end_time":"2025-01-20T18:00:00+09:00"}'

# 指定時間帯の可用性確認
curl "http://localhost:8000/api/availability?start=2025-01-20T12:00:00Z&end=2025-01-20T20:00:00Z"
```

## 運用メモ
- CORS はデフォルト許可 (`cors_origins=["*"]`)。必要に応じて `backend/app/config.py` または `.env` で絞り込んでください。
- DBは `backend/data/gpu_reservations.db` に作成されます。リセットしたい場合はファイルを削除し、必要なら `backend.app.seed` を再実行してください。
- 追加依存の導入は `uv add パッケージ名` を利用してください。
- 本リポジトリはバックエンドのみを提供します。フロントエンドからは上記 REST API を利用してください。
