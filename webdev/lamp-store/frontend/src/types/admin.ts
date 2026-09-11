import type { ISODateTime, UUID } from './common';
import type { RoleName } from './enums';

/**
 * Администратор без password_hash (AdminRead / MeResponse).
 *
 * ДОПУЩЕНИЕ: `schemas/admin.py` не был прислан — состав полей взят по
 * аналогии с ORM-моделью `admins` из project_context, за вычетом
 * `password_hash` (он не покидает admin_service по domain_decisions).
 * Сверить при первом вызове GET /auth/me.
 */
export interface AdminRead {
  admin_id: UUID;
  email: string;
  full_name: string;
  role_name: RoleName;
  is_active: boolean;
  failed_login_attempts: number;
  locked_until: ISODateTime | null;
  last_login: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface LoginRequest {
  email: string;
  password: string;
}

/** Ответ POST /auth/login (TokenResponse). Refresh-токена нет — только повторный вход. */
export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}

/**
 * ДОПУЩЕНИЕ: эндпоинты управления другими админами (`admins.py`) не были
 * прислан. Типы ниже — черновик по аналогии с остальными admin-CRUD
 * ресурсами (products/categories), сверить при получении реального файла.
 */
export interface AdminCreateRequest {
  email: string;
  password: string;
  full_name: string;
  role_name: RoleName;
}

export interface RoleChangeRequest {
  new_role: RoleName;
}
