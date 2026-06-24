import type { Metadata } from 'next'
import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter'
import Providers from './providers'

export const metadata: Metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME || 'Property Sale Screening',
  description: '不動産売却先スクリーニングシステム',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>
        <AppRouterCacheProvider>
          <Providers>{children}</Providers>
        </AppRouterCacheProvider>
      </body>
    </html>
  )
}
