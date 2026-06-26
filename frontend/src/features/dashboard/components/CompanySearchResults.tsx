'use client'

import { Alert, Box, Chip, Stack, Typography } from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'

import { CompanyRankingTable } from './CompanyRankingTable'
import {
  CompanySearchError,
  type CompanyRankingItemSchema,
  type CompanySearchResponse,
} from '@/features/companies'

export interface CompanySearchResultsProps {
  data: CompanySearchResponse | undefined
  isLoading: boolean
  error: CompanySearchError | null
}

function errorMessage(error: CompanySearchError): string {
  switch (error.code) {
    case 'NL_PARSE_FAILED':
      return 'クエリを解釈できませんでした。別の表現をお試しください'
    case 'QUERY_TOO_LONG':
      return '検索クエリは200字以内で入力してください'
    case 'LLM_CALL_FAILED':
      return '検索処理に失敗しました。しばらくして再度お試しください'
    default:
      return '検索に失敗しました'
  }
}

export function CompanySearchResults({
  data,
  isLoading,
  error,
}: CompanySearchResultsProps) {
  if (error) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        {errorMessage(error)}
      </Alert>
    )
  }

  const items: CompanyRankingItemSchema[] = data?.items ?? []

  return (
    <Box>
      {data?.search_summary && (
        <Alert
          icon={<AutoAwesomeIcon fontSize="inherit" />}
          severity="info"
          sx={{ mb: 2 }}
        >
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            flexWrap="wrap"
          >
            <Typography variant="body2">{data.search_summary}</Typography>
            <Chip
              label={`${data.total}件`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Stack>
        </Alert>
      )}

      {!isLoading && items.length === 0 ? (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ py: 4, textAlign: 'center' }}
        >
          条件に一致する企業がありません
        </Typography>
      ) : (
        <CompanyRankingTable items={items} isLoading={isLoading} />
      )}
    </Box>
  )
}
