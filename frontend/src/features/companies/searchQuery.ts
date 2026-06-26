/**
 * Companies feature - 検索クエリ分類ロジック
 *
 * ユーザー入力を「証券コード完全一致 / 企業名完全一致 / 自然言語検索」に分類する。
 */

export type SearchQueryKind = 'securities_code' | 'company_name' | 'nl'

export interface ClassifiedQuery {
  kind: SearchQueryKind
  value: string
}

/** 自然言語クエリを示唆するキーワード */
const NL_MARKERS = [
  '以上',
  '以下',
  '未満',
  '割れ',
  '含み益',
  'PBR',
  'スコア',
  '業種',
  '地域',
  '億',
  '倍',
  '企業',
]

/**
 * 入力文字列を検索種別に分類する。
 *
 * - 4〜5桁の数字 → 証券コード（完全一致）
 * - 条件キーワード / 空白を含む / 長い → 自然言語
 * - それ以外の短い文字列 → 企業名（完全一致）
 */
export function classifyQuery(raw: string): ClassifiedQuery | null {
  const value = raw.trim()
  if (value === '') return null

  if (/^\d{4,5}$/.test(value)) {
    return { kind: 'securities_code', value }
  }

  const looksNatural =
    value.length > 12 ||
    /\s/.test(value) ||
    NL_MARKERS.some((marker) => value.includes(marker))

  if (looksNatural) {
    return { kind: 'nl', value }
  }

  return { kind: 'company_name', value }
}
