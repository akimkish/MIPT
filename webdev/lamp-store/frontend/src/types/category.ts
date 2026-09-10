import type { ISODateTime, UUID } from './common';

/**
 * Категория товаров каталога.
 *
 * ДОПУЩЕНИЕ: `schemas/category.py` не был прислан, поле-состав взят по
 * аналогии с ORM-моделью `categories` из project_context (category_id,
 * name, description, is_active, created_at, updated_at) и по тому, как
 * `CategoryRead` используется в `api/v1/categories.py`. Сверить при
 * первом реальном вызове.
 */
export interface Category {
  category_id: UUID;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

/** Тело POST /admin/categories — по аналогии с ProductCreate/PromoCreate. */
export interface CategoryCreateRequest {
  name: string;
  description?: string;
}

/** Тело PATCH /admin/categories/{id}. */
export type CategoryUpdateRequest = Partial<CategoryCreateRequest> & {
  is_active?: boolean;
};
