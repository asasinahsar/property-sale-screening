/**
 * Auth feature - Data Access Layer
 *
 * orval 生成の fetch 関数を wrap し、Cookie 認証（credentials: include）を付与する。
 * 生成コード（shared/api/generated）は編集禁止のため、ここで薄くラップする。
 */
import {
  getMeApiV1AuthMeGet,
  loginApiV1AuthLoginPost,
  logoutApiV1AuthLogoutPost,
} from '@/shared/api/generated/propertySaleScreeningAPI'
import type {
  LoginRequest,
  MeResponse,
} from '@/shared/api/generated/propertySaleScreeningAPI'

const withCredentials: RequestInit = { credentials: 'include' }

export async function login(body: LoginRequest): Promise<void> {
  const res = await loginApiV1AuthLoginPost(body, withCredentials)
  if (res.status >= 400) {
    throw new Error(String(res.status))
  }
}

export async function logout(): Promise<void> {
  await logoutApiV1AuthLogoutPost(withCredentials)
}

export async function getMe(): Promise<MeResponse> {
  const res = await getMeApiV1AuthMeGet(withCredentials)
  if (res.status >= 400) {
    throw new Error(String(res.status))
  }
  return res.data as MeResponse
}

export type { LoginRequest, MeResponse }
