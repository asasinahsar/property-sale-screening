# TDD（テスト駆動開発）ガイド

## 概要

**テスト駆動開発（TDD）** は、以下の 3つのフェーズを厳密に順守する開発手法です。

```
🔴 RED    → 🟢 GREEN  → 🔵 REFACTOR
(テスト)    (実装)       (改善)
```

## Red-Green-Refactor サイクル

### Phase 1: 🔴 RED - テストを先に書く
- 実装する前にテストを書く
- テストは失敗する状態から始める

### Phase 2: 🟢 GREEN - テストを通す
- テストを通すための実装をする
- きれいさは後回し

### Phase 3: 🔵 REFACTOR - コードを改善
- テストはそのまま
- コードを改善、重複排除、命名改善など

## ルール

### ✅ 必ず守る
- 🔴 → 🟢 → 🔵 の順序
- 各フェーズを順番に進める
- テストが全て pass することを常に確認

### ❌ 絶対にしてはいけないこと
- テストなしで実装を始める
- テストを修正してコードを通す
- REFACTOR フェーズを省略する
- 複数機能を同時に開発する

## 3レイヤー別テスト

各層ごとに独立したテストを書く：

- **Presentation層**: API/UI のテスト（下層をモック）
  - 参照: `docs/requirements/ui.md`（画面仕様）、`docs/requirements/api.md`（API仕様）
- **Business Logic層**: ドメインロジックのテスト（DB をモック）
  - 参照: `docs/requirements/functions.md`（機能・ビジネスルール）
- **Data Access層**: DB操作のテスト（実DB またはメモリDB）
  - 参照: `docs/requirements/data.md`（データスキーマ・仕様）

## 各段階の詳細

各フェーズの詳細な実行は、以下のエージェントが担当します：

| エージェント | 役割 |
|------------|------|
| **backend-test-writer** / **frontend-test-writer** | 🔴 RED：失敗するテストを書く |
| **backend-{repository,service,api}-layer** / **frontend-{component-builder,feature-writer}** | 🟢 GREEN：テストを通す実装 |
| **backend-{repository,service,api}-layer** / **frontend-{component-builder,feature-writer}** | 🔵 REFACTOR：コード改善 |

詳細な指示は各エージェントの定義を参照してください。
