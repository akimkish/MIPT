import type { DecimalString, ISODateTime, UUID } from './common';
import type { DiscountType } from './enums';

/** Промо-акция на товар. */
export interface Promo {
  promo_id: UUID;
  promo_name: string;
  description: string | null;
  discount_type: DiscountType;
  discount: DecimalString;
  product_id: UUID;
  min_quantity: number;
  valid_from: ISODateTime;
  valid_to: ISODateTime;
  is_active: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

/** Тело POST /admin/promos (PromoCreate). `min_quantity` необязателен — default 1. */
export interface PromoCreateRequest {
  promo_name: string;
  description?: string;
  discount_type: DiscountType;
  discount: DecimalString;
  product_id: UUID;
  min_quantity?: number;
  valid_from: ISODateTime;
  valid_to: ISODateTime;
}

/**
 * Тело PATCH /admin/promos/{id} (PromoUpdate).
 *
 * ВАЖНО: `product_id` здесь НЕТ вообще — привязку акции к другому товару
 * сменить нельзя, только пересоздать акцию.
 */
export type PromoUpdateRequest = Partial<Omit<PromoCreateRequest, 'product_id'>> & {
  is_active?: boolean;
};

/**
 * Фильтр GET /admin/promos.
 *
 * `product_id` ОБЯЗАТЕЛЕН на бэкенде (`Query(...)` без default) — общего
 * списка всех акций сразу по всем товарам эндпоинт не отдаёт. Экран
 * "Промо" в админке должен сперва предложить выбрать товар.
 */
export interface AdminPromoFilters {
  product_id: UUID;
  limit?: number;
  offset?: number;
}
