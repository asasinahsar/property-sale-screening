'use client'

import Link from 'next/link'
import { Box, Card, CardActionArea, Chip, Stack, Typography } from '@mui/material'

import type { RecentEventSchema } from '../api'

export interface RecentEventsBannerProps {
  events: RecentEventSchema[]
  isLoading: boolean
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  new_disclosure: '開示',
  large_shareholding: '大量保有',
}

const EVENT_TYPE_COLORS: Record<string, 'info' | 'warning'> = {
  new_disclosure: 'info',
  large_shareholding: 'warning',
}

function eventTypeLabel(eventType: string): string {
  return EVENT_TYPE_LABELS[eventType] ?? eventType
}

export function RecentEventsBanner({
  events,
  isLoading,
}: RecentEventsBannerProps) {
  // ローディング中・イベントなしのときは非表示
  if (isLoading || events.length === 0) {
    return null
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        直近イベント
      </Typography>
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          overflowX: 'auto',
          pb: 1,
        }}
      >
        {events.map((event) => (
          <Card
            key={`${event.company_id}-${event.event_type}-${event.occurred_at}`}
            variant="outlined"
            sx={{ minWidth: 220, flexShrink: 0 }}
          >
            <CardActionArea
              component={Link}
              href={`/companies/${event.company_id}`}
              sx={{ p: 2, height: '100%' }}
            >
              <Stack spacing={1}>
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                >
                  <Chip
                    label={eventTypeLabel(event.event_type)}
                    size="small"
                    color={EVENT_TYPE_COLORS[event.event_type] ?? 'default'}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {event.occurred_at}
                  </Typography>
                </Stack>
                <Typography variant="subtitle1" fontWeight="bold" noWrap>
                  {event.company_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {event.securities_code}
                  {event.event_score != null && (
                    <Box component="span" sx={{ ml: 1 }}>
                      スコア {event.event_score.toFixed(1)}
                    </Box>
                  )}
                </Typography>
              </Stack>
            </CardActionArea>
          </Card>
        ))}
      </Box>
    </Box>
  )
}
