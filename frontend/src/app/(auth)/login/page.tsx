import { Box } from '@mui/material'

import { LoginForm } from '@/features/auth'

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
      <Box
        sx={{ p: 4, bgcolor: 'white', borderRadius: 2, boxShadow: 1, width: 400 }}
      >
        <LoginForm />
      </Box>
    </Box>
  )
}
