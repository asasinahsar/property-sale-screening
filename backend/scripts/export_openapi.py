"""FastAPI OpenAPI スキーマをエクスポート（Slice 0-6 の orval 連携用）

デフォルト出力先は backend/openapi.json。
これは frontend/orval.config.ts の input（../backend/openapi.json）と一致させるため。
スクリプトはどこから実行しても backend/openapi.json に出力される（__file__ 基準）。
"""
import argparse
import json
from pathlib import Path

from app.main import app

# backend/ ディレクトリ（このスクリプトの2つ上の親）
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BACKEND_DIR / "openapi.json"


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    schema = app.openapi()
    with open(args.output, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"OpenAPI schema exported to: {args.output}")


if __name__ == "__main__":
    main()
