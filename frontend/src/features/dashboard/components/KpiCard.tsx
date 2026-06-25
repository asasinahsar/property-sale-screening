'use client'

import { Box, Card, CardContent, Typography } from '@mui/material'

export interface KpiCardProps {
  title: string
  value: string | number
  color?: string
}

export function KpiCard({ title, value, color = 'primary.main' }: KpiCardProps) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'baseline',
            borderLeft: 4,
            borderColor: color,
            pl: 1.5,
          }}
        >
          <Typography variant="h4" fontWeight="bold" sx={{ color }}>
            {value}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}
