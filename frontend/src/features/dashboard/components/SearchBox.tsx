'use client'

import { useState } from 'react'
import { Box, IconButton, InputAdornment, TextField, Typography } from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import ClearIcon from '@mui/icons-material/Clear'

import { classifyQuery } from '@/features/companies'
import type { ClassifiedQuery } from '@/features/companies'

const MAX_LENGTH = 200

const PLACEHOLDER =
  '企業名・コード、または「含み益500億以上の小売業」などで検索'

export interface SearchBoxProps {
  /** 検索実行時に分類済みクエリを通知する */
  onSearch: (query: ClassifiedQuery) => void
  /** 空入力で確定したとき（検索クリア）に呼ばれる */
  onClear?: () => void
  /** 初期値（URL からの復元など） */
  initialValue?: string
}

export function SearchBox({ onSearch, onClear, initialValue = '' }: SearchBoxProps) {
  const [value, setValue] = useState(initialValue)

  const submit = () => {
    const classified = classifyQuery(value)
    if (classified === null) {
      onClear?.()
      return
    }
    onSearch(classified)
  }

  const handleClear = () => {
    setValue('')
    onClear?.()
  }

  return (
    <Box sx={{ mb: 2 }}>
      <TextField
        fullWidth
        size="small"
        value={value}
        placeholder={PLACEHOLDER}
        onChange={(e) => setValue(e.target.value.slice(0, MAX_LENGTH))}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            submit()
          }
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon fontSize="small" color="action" />
            </InputAdornment>
          ),
          endAdornment: value !== '' && (
            <InputAdornment position="end">
              <IconButton
                aria-label="検索をクリア"
                size="small"
                onClick={handleClear}
                edge="end"
              >
                <ClearIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'flex-end',
          mt: 0.5,
        }}
      >
        <Typography
          variant="caption"
          color={value.length >= MAX_LENGTH ? 'error' : 'text.secondary'}
        >
          {value.length} / {MAX_LENGTH}
        </Typography>
      </Box>
    </Box>
  )
}
