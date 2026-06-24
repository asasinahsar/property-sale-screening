import { Box, Typography } from '@mui/material'

export default function LoginPage() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'grey.100',
      }}
    >
      <Box sx={{ p: 4, bgcolor: 'white', borderRadius: 2, boxShadow: 1, width: 400 }}>
        <Typography variant="h5" fontWeight="bold" mb={3}>
          ログイン
        </Typography>
        <Typography variant="body2" color="text.secondary">
          ログインフォームは Slice 1 以降で実装されます
        </Typography>
      </Box>
    </Box>
  )
}
