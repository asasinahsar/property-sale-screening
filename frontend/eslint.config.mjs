import { dirname } from 'path'
import { fileURLToPath } from 'url'
import { FlatCompat } from '@eslint/eslintrc'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const compat = new FlatCompat({ baseDirectory: __dirname })

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'next-env.d.ts', // Next.js 自動生成
      'next.config.ts',
      'orval.config.ts', // orval 設定（anonymous default export を許容）
      'jest.config.ts',
      'src/shared/api/generated/**', // orval 自動生成（編集禁止・lint 対象外）
    ],
  },
  {
    // FSD: feature 間の直接 import を禁止（index.ts 経由のみ許可）
    files: ['src/features/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: [
                '@/features/*/*', // 他 feature の内部ファイルへの直接 import
                '../*/!(index)', // 兄弟 feature の内部への相対 import
                '../*/!(index)/**',
              ],
              message:
                'feature 間は index.ts（barrel export）経由でのみ import してください（FSD ルール）。',
            },
          ],
        },
      ],
    },
  },
]

export default eslintConfig
