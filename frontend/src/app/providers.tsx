'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, CssBaseline, createTheme } from '@mui/material'
import { queryClient } from '@/lib/queryClient'

const theme = createTheme()

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  )
}
