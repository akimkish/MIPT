import type {
  AdminCreateRequest,
  AdminRead,
  LoginRequest,
  RoleChangeRequest,
  TokenResponse,
} from '../types/admin';
import { createHttpClient } from './httpClient';

const client = createHttpClient(import.meta.env.VITE_ADMIN_API_URL);

export function login(body: LoginRequest): Promise<TokenResponse> {
  return client.post<TokenResponse>('/api/v1/auth/login', body);
}

/**
 * Профиль администратора, выписавшего переданный токен.
 *
 * Закрывает открытый вопрос предыдущего шага: claims в самом JWT
 * decode-ить на клиенте не нужно — есть выделенный эндпоинт `/auth/me`.
 */
export function getMe(token: string): Promise<AdminRead> {
  return client.get<AdminRead>('/api/v1/auth/me', { token });
}

/**
 * ДОПУЩЕНИЕ: файл `admins.py` (управление другими админами) не был
 * прислан. Функции ниже — черновик по аналогии с остальными admin-CRUD
 * ресурсами (products/categories/manufacturers). Пути и формы точно
 * сверить, когда файл будет доступен.
 */

export function getAdmins(token: string): Promise<AdminRead[]> {
  return client.get<AdminRead[]>('/api/v1/admins', { token });
}

export function createAdmin(body: AdminCreateRequest, token: string): Promise<AdminRead> {
  return client.post<AdminRead>('/api/v1/admins', body, { token });
}

/** Деактивированный админ сохраняет доступ до истечения TTL уже выданного токена
 * (осознанное упрощение, known_limitations #3) — это не баг фронта. */
export function deactivateAdmin(adminId: string, token: string): Promise<void> {
  return client.delete<void>(`/api/v1/admins/${adminId}`, { token });
}

export function changeAdminRole(
  adminId: string,
  body: RoleChangeRequest,
  token: string,
): Promise<AdminRead> {
  return client.patch<AdminRead>(`/api/v1/admins/${adminId}/role`, body, { token });
}
