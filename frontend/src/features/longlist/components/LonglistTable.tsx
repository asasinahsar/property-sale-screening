'use client'

import { useState } from 'react'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'

import { useGetMe } from '@/features/auth'

import {
  useDeleteFromLonglist,
  useExportLonglist,
  useLonglist,
  useSetApproval,
  useUpdateLonglist,
} from '../hooks'
import type { LonglistItemSchema, LonglistStatus } from '../types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<
  LonglistStatus,
  'default' | 'success' | 'error'
> = {
  candidate: 'default',
  approved: 'success',
  rejected: 'error',
}

const COLUMNS = [
  'Company (Code)',
  'Industry',
  'Total',
  'Structure',
  'Event',
  'Unrealized Gain',
  'Memo',
  'Status',
  'Actions',
] as const

function fmtNum(value: number | null | undefined, digits = 1): string {
  return value != null ? value.toFixed(digits) : '—'
}

// ---------------------------------------------------------------------------
// Memo cell (inline edit)
// ---------------------------------------------------------------------------

function MemoCell({ item }: { item: LonglistItemSchema }) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(item.reason_memo ?? '')
  const { mutate: updateMutate, isPending } = useUpdateLonglist()

  const handleSave = () => {
    updateMutate({ itemId: item.id, body: { reason_memo: value } })
    setEditing(false)
  }

  if (editing) {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <TextField
          size="small"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          inputProps={{ maxLength: 500, 'aria-label': 'memo-input' }}
          multiline
          maxRows={3}
        />
        <Button size="small" onClick={handleSave} disabled={isPending}>
          Save
        </Button>
      </Stack>
    )
  }

  return (
    <Box
      onClick={() => setEditing(true)}
      sx={{ cursor: 'pointer', minWidth: 80, color: item.reason_memo ? 'inherit' : 'text.secondary' }}
    >
      {item.reason_memo || 'Add memo'}
    </Box>
  )
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function LonglistTable() {
  const { data, isLoading } = useLonglist()
  const { data: me } = useGetMe()
  const isManager = me?.role === 'manager'

  const { mutate: approvalMutate } = useSetApproval()
  const { mutate: deleteMutate } = useDeleteFromLonglist()
  const { mutate: exportMutate, isPending: isExporting } = useExportLonglist()

  const [deleteTarget, setDeleteTarget] = useState<LonglistItemSchema | null>(
    null,
  )

  const handleConfirmDelete = () => {
    if (deleteTarget) {
      deleteMutate({ itemId: deleteTarget.id })
      setDeleteTarget(null)
    }
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  const items = data?.items ?? []

  return (
    <Box sx={{ p: 3 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 2 }}
      >
        <Typography variant="h5" fontWeight="bold">
          Longlist
        </Typography>
        <Button
          variant="contained"
          onClick={() => exportMutate()}
          disabled={isExporting || items.length === 0}
          aria-label="Export CSV"
        >
          Export CSV
        </Button>
      </Stack>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              {COLUMNS.map((col) => (
                <TableCell key={col}>{col}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id} hover>
                <TableCell>
                  {item.name}
                  <Box
                    component="span"
                    sx={{ ml: 0.5, color: 'text.secondary', fontSize: '0.75rem' }}
                  >
                    ({item.securities_code})
                  </Box>
                </TableCell>
                <TableCell>{item.industry}</TableCell>
                <TableCell align="right">{fmtNum(item.total_score)}</TableCell>
                <TableCell align="right">
                  {fmtNum(item.structure_score)}
                </TableCell>
                <TableCell align="right">{fmtNum(item.event_score)}</TableCell>
                <TableCell align="right">
                  {item.unrealized_gain != null
                    ? item.unrealized_gain.toLocaleString()
                    : '—'}
                </TableCell>
                <TableCell>
                  <MemoCell item={item} />
                </TableCell>
                <TableCell>
                  <Chip
                    label={item.status}
                    color={STATUS_COLORS[item.status as LonglistStatus]}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      color="success"
                      variant="outlined"
                      disabled={!isManager}
                      onClick={() =>
                        approvalMutate({ itemId: item.id, action: 'approve' })
                      }
                      aria-label={`approve-${item.id}`}
                    >
                      Approve
                    </Button>
                    <Button
                      size="small"
                      color="warning"
                      variant="outlined"
                      disabled={!isManager}
                      onClick={() =>
                        approvalMutate({ itemId: item.id, action: 'reject' })
                      }
                      aria-label={`reject-${item.id}`}
                    >
                      Reject
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      variant="outlined"
                      onClick={() => setDeleteTarget(item)}
                      aria-label={`delete-${item.id}`}
                    >
                      Delete
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={COLUMNS.length} align="center">
                  No items in the longlist
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={deleteTarget !== null} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Remove from longlist</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Remove {deleteTarget?.name} from the longlist?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button color="error" onClick={handleConfirmDelete} autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
