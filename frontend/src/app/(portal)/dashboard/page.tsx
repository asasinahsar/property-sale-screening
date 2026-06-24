import { Box, Typography, Alert } from '@mui/material'

export default function DashboardPage() {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        ダッシュボード
      </Typography>
      <Alert severity="info">
        ダッシュボードコンテンツは Slice 1 以降で実装されます
      </Alert>
    </Box>
  )
}
