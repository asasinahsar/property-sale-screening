"""FastAPI OpenAPI スキーマをエクスポート（Slice 0-6 の orval 連携用）"""
import argparse
import json

from app.main import app


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument("-o", "--output", default="openapi.json")
    args = parser.parse_args()

    schema = app.openapi()
    with open(args.output, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"OpenAPI schema exported to: {args.output}")


if __name__ == "__main__":
    main()
