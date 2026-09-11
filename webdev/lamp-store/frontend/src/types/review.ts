import type { ISODateTime, UUID } from './common';

/** Отзыв на товар. На витрине показываются только is_approved === true. */
export interface Review {
  review_id: UUID;
  product_id: UUID;
  user_name: string;
  user_email: string;
  description: string | null;
  /** Целое число от 1 до 5. */
  rating: number;
  is_approved: boolean;
  created_at: ISODateTime;
}

/**
 * Тело POST /products/{product_id}/reviews (ReviewCreate).
 *
 * `product_id` ОБЯЗАН присутствовать в теле и совпадать с `product_id`
 * из пути — бэкенд явно сверяет их и отдаёт 400 при несовпадении
 * (см. `create_review` в reviews.py). Это легко забыть при сборке формы.
 */
export interface ReviewCreateRequest {
  product_id: UUID;
  user_name: string;
  user_email: string;
  description?: string;
  rating: number;
}

/** Тело PATCH /admin/reviews/{id} — публикация/снятие с публикации. */
export interface ReviewModerateRequest {
  is_approved: boolean;
}
