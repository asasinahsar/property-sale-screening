---
name: foundation-frontend-setup
description: Vite + React 19 + Material-UI フロントエンド初期化・ディレクトリ構造・開発環境設定
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Slice 0-5: Frontend Setup (Vite + React 19 + MUI)

Vite + React 19 + Material-UI フロントエンド初期化・ディレクトリ構造構築・開発環境設定を行うスキル。

## Purpose

フロントエンド開発を始めるための基盤を整備する：

1. Vite + React 19 プロジェクト初期化
2. ディレクトリ構造の作成（3レイヤーアーキテクチャに基づく）
3. Material-UI v5 インストール・基本設定
4. Vitest + React Testing Library 設定
5. API client 基盤実装
6. TanStack Query (React Query) 設定（データ管理）
7. orval 設定（OpenAPI から API client 自動生成）

## When to use

- Sprint を開始して、バックエンド基盤が完成した後に実行
- フロントエンド全体の基盤を整備したい
- React 開発環境を初期化したい

## Prerequisites

- Slice 0-1 ～ 0-4（バックエンド基盤）が完了していること
- Node.js v18+ がインストールされていること

## Outputs

プロジェクト構造：
```
frontend/
├── src/
│   ├── pages/                      # ページコンポーネント
│   │   └── index.tsx
│   ├── components/                 # UIコンポーネント
│   │   └── Layout.tsx
│   ├── features/                   # 機能別フォルダ
│   │   ├── auth/                   # 認証機能
│   │   │   ├── hooks/              # useLogin など
│   │   │   ├── components/
│   │   │   └── services/
│   │   └── users/                  # ユーザー管理
│   │       ├── hooks/              # useCurrentUser など
│   │       ├── components/
│   │       └── services/
│   ├── hooks/                      # グローバルフック
│   │   └── useAuth.ts
│   ├── shared/                     # 共有モジュール
│   │   ├── api/
│   │   │   ├── mutator.ts          # orval custom mutator
│   │   │   └── generated.ts        # orval で自動生成
│   │   └── ...
│   ├── services/                   # API client（orval 生成）
│   │   └── api/
│   │       └── generated.ts        # 自動生成ファイル
│   ├── lib/
│   │   ├── queryClient.ts          # TanStack Query設定
│   │   ├── auth/                   # 認証ロジック
│   │   └── utils/                  # ユーティリティ
│   ├── context/                    # Context API
│   │   └── AuthContext.tsx
│   ├── types/                      # 共通型定義
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
├── tests/
│   ├── unit/
│   ├── integration/
│   └── vitest.config.ts
├── public/
├── .env.example
├── package.json
├── vite.config.ts
├── tsconfig.json
├── vitest.config.ts
├── orval.config.ts                 # orval 設定（custom mutator指定）
└── README.md
```

## Procedure

### Step 1: Node.js 環境確認

```bash
# Node.js バージョン確認（v18+ 推奨）
node --version
npm --version
```

### Step 2: Vite + React プロジェクト初期化

```bash
cd training-sprint2

# Vite プロジェクト作成
npm create vite@latest frontend -- --template react-ts

# フォルダに移動
cd frontend

# 依存パッケージをインストール
npm install
```

### Step 3: ディレクトリ構造を作成

```bash
cd frontend

# フォルダ作成
mkdir -p src/pages
mkdir -p src/components
mkdir -p src/features/{auth,users}
mkdir -p src/features/auth/{hooks,components,services}
mkdir -p src/features/users/{hooks,components,services}
mkdir -p src/hooks
mkdir -p src/shared/api              # orval custom mutator
mkdir -p src/services/api            # orval 自動生成先
mkdir -p src/lib/{queryClient,auth,utils}
mkdir -p src/context
mkdir -p src/types
mkdir -p tests/{unit,integration}
```

### Step 4: TypeScript 設定を更新

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "strict": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/pages/*": ["./src/pages/*"],
      "@/components/*": ["./src/components/*"],
      "@/features/*": ["./src/features/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/services/*": ["./src/services/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/context/*": ["./src/context/*"],
      "@/types/*": ["./src/types/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "build"]
}
```

### Step 5: Vite 設定を更新

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### Step 6: Material-UI v7 をインストール

```bash
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material
npm install -D @mui/types
```

### Step 7: Vitest + React Testing Library を設定

```bash
npm install -D vitest @vitest/ui @testing-library/react @testing-library/jest-dom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

```typescript
// tests/setup.ts
import '@testing-library/jest-dom'
```

### Step 8: TanStack Query (React Query) をインストール

```bash
npm install @tanstack/react-query
```

### Step 9: orval 設定の確認（自動配置済み）

`/r2b-build-sprint2` スキル実行時に、以下のファイルが自動配置されます：

- **orval.config.ts** - プロジェクトルート
  （custom mutator を参照するorval設定）

- **frontend/src/shared/api/mutator.ts** - フロントエンド
  （httpOnly Cookie + トークン自動更新対応）

**設定の確認**:

```bash
# orval.config.ts が配置されているか確認
cat orval.config.ts

# mutator.ts が配置されているか確認
cat frontend/src/shared/api/mutator.ts
```

### Step 10: orval 依存パッケージをインストール

```bash
npm install -D orval
```

### Step 11: orval で API client を自動生成

```bash
# OpenAPI スキーマから API client を生成
npm run orval

# または手動実行
npx orval
```

**生成されるファイル**:
- `frontend/src/services/api/generated.ts` - OpenAPI スキーマから自動生成された API client

> **重要**:
> - バックエンド（FastAPI）で OpenAPI スキーマを自動生成することが前提
> - API 起動後、http://localhost:8000/openapi.json で確認可能
> - mutator.ts は自動配置済みなので、手動で作成不要

### Step 12: TanStack Query 設定と App.tsx 実装

```typescript
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})
```

```typescript
// src/App.tsx
import { QueryClientProvider } from '@tanstack/react-query'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import Layout from '@/components/Layout'
import Home from '@/pages/Home'
import { queryClient } from '@/lib/queryClient'

const theme = createTheme()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Layout>
          <Home />
        </Layout>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
```

### Step 13: orval 生成 API client を使用（例）

orval で自動生成された API client を TanStack Query と組み合わせて使用：

```typescript
// src/features/auth/hooks/useLogin.ts
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
// orval で生成された API client
import { postApiV1AuthLogin } from '@/services/api/generated'

export const useLogin = () => {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      postApiV1AuthLogin(credentials),
    onSuccess: () => {
      // ログイン成功 → ダッシュボードへリダイレクト
      navigate('/dashboard')
    },
    onError: (error) => {
      console.error('Login failed:', error)
      // エラーハンドリング
    },
  })
}
```

```typescript
// src/features/users/hooks/useCurrentUser.ts
import { useQuery } from '@tanstack/react-query'
// orval で生成された API client
import { getApiV1UsersMe } from '@/services/api/generated'

export const useCurrentUser = () => {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: () => getApiV1UsersMe(),
    retry: 1,
  })
}
```

### Step 14: 基本レイアウトコンポーネントを実装

```typescript
// src/components/Layout.tsx
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material'
import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            R2B Training
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4, flex: 1 }}>
        {children}
      </Container>

      <Box component="footer" sx={{ bgcolor: '#f5f5f5', py: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          © 2026 R2B Training Platform
        </Typography>
      </Box>
    </Box>
  )
}
```

```typescript
// src/pages/Home.tsx
import { Typography, Box, Alert } from '@mui/material'

export default function Home() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome to R2B Training (Frontend)
      </Typography>
      <Typography variant="body1" paragraph>
        フロントエンドセットアップが完了しました。
      </Typography>
      <Alert severity="info">
        バックエンド API に接続すると、ここに動的コンテンツが表示されます。
      </Alert>
    </Box>
  )
}
```

### Step 15: 認証フック（例）を実装

```typescript
// src/features/auth/hooks/useAuth.ts
// 注: httpOnly Cookie ベースの認証なので、トークン管理は不要
// API client（orval custom mutator）が自動的に Cookie を処理します

import { useState, useCallback } from 'react'
import apiClient from '@/lib/api/client'

export const useAuth = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      // Cookie は自動的に orval custom mutator で処理される
      // クライアント側でトークンを管理する必要はない
      const response = await apiClient.post('/api/v1/auth/login', {
        email,
        password,
      })
      return response.data
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Login failed'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    // サーバー側で Cookie をクリア
    try {
      await apiClient.post('/api/v1/auth/logout')
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }, [])

  return { login, logout, loading, error }
}
```

### Step 16: .env.example を作成

```bash
# .env.example
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=R2B Training
```

### Step 17: README.md を作成

```markdown
# Training Sprint 2 - Frontend (Vite + React)

## プロジェクト説明
Vite + React 19 + Material-UI による SPA フロントエンド

## セットアップ

### 1. 依存パッケージをインストール
\`\`\`bash
cd frontend
npm install
\`\`\`

### 2. 開発サーバー起動
\`\`\`bash
npm run dev
\`\`\`

### 3. ブラウザで開く
http://localhost:5173

## ディレクトリ構造
- pages/: ページコンポーネント
- components/: 共有 UI コンポーネント
- features/: 機能別フォルダ（auth, users など）
- services/: API client（orval 生成）
- hooks/: カスタムフック
- lib/: ユーティリティ

## 開発コマンド
- \`npm run dev\`: 開発サーバー起動
- \`npm run build\`: ビルド
- \`npm run preview\`: ビルド結果プレビュー
- \`npm run test\`: テスト実行

## API 連携
- バックエンド: http://localhost:8000
- orval で OpenAPI スキーマから client を自動生成
- TanStack Query でデータ管理

## 認証
- JWT (Authorization Header) / Cookie のいずれかをサポート
- API リクエストに自動的にトークン付与

## 開発時の留意点
- 3レイヤーアーキテクチャを遵守
- TDD で実装
- Material-UI の Design System を活用
```

### Step 18: package.json に orval スクリプトを追加

```json
// package.json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "orval": "orval",  // 追加
    "orval:watch": "orval --watch"  // 追加（開発時オプション）
  }
}
```

### Step 19: 環境変数を設定

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=R2B Training
```

### Step 20: 開発環境確認

```bash
# ビルド確認
npm run build

# orval で API client を自動生成
npm run orval

# 開発サーバー起動
npm run dev
```

**確認項目**:
- [ ] ビルドが成功する
- [ ] `npm run orval` で src/services/api/generated.ts が生成される
- [ ] http://localhost:5173 にアクセスできる
- [ ] ホームページが表示される
- [ ] Material-UI のスタイルが適用されている
- [ ] orval 生成 API client が import できる

## チェックリスト

### Slice 0-5 完了時

- [ ] Vite + React 19 プロジェクト初期化完了
- [ ] ディレクトリ構造を作成した（src/shared/api 含む）
- [ ] TypeScript 設定完了（パスエイリアス @/ 設定）
- [ ] Material-UI v7 インストール・設定完了
- [ ] Vitest + React Testing Library 設定完了
- [ ] TanStack Query インストール・設定完了

- [ ] **⭐ orval custom mutator は自動配置済み**
  - [x] src/shared/api/mutator.ts （r2b-build-sprint2 でコピー）
  - [x] credentials: include 設定済み
  - [x] 401 時の自動トークンリフレッシュ実装済み
  - [x] ログイン失敗時のリダイレクト実装済み

- [ ] **⭐ orval.config.ts は自動配置済み**
  - [x] プロジェクトルートに配置（r2b-build-sprint2 でコピー）
  - [x] custom mutator を参照

- [ ] orval パッケージをインストール（npm install -D orval）
- [ ] **orval で OpenAPI から API client を自動生成**
  - [ ] npm run orval 実行
  - [ ] frontend/src/services/api/generated.ts が生成される

- [ ] TanStack Query queryClient を設定（src/lib/queryClient.ts）
- [ ] App.tsx に QueryClientProvider を設定
- [ ] orval 生成 API client を使用するフック実装（useLogin など）
- [ ] 基本レイアウトコンポーネント実装完了
- [ ] .env.example 作成完了（VITE_API_BASE_URL 設定）
- [ ] package.json に orval スクリプトを追加
- [ ] ビルド・開発サーバー起動確認完了
- [ ] orval 生成 API client をインポート・使用確認完了
- [ ] README.md 作成完了

### 次のステップ

Slice 0-5 完了後は、**Slice 0-6: API Integration Test を実行**

```
Slice 0-1: FastAPI セットアップ
Slice 0-2: PostgreSQL Docker
Slice 0-3: Database Design & Implementation
Slice 0-4: Authentication Middleware (JWT/Cookie)
  ↓
Slice 0-5（ここ）
  ↓
Slice 0-6: API Integration Test
  ↓
Phase 1: 基本機能実装へ
```

## 参考資料

- [Vite Documentation](https://vitejs.dev/)
- [React 19 Documentation](https://react.dev/)
- [Material-UI v7 Documentation](https://mui.com/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [orval Documentation](https://orval.dev/)
- [Vitest Documentation](https://vitest.dev/)
