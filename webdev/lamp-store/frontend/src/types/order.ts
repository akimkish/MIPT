import type { DecimalString, ISODateTime, UUID } from './common';
import type { OrderStatus } from './enums';

/**
 * Позиция заказа в ответах API — неизменяемый снимок товара.
 *
 * ДОПУЩЕНИЕ: `schemas/order_item.py` не был прислан, состав полей взят
 * из ORM-модели `order_items` в project_context (совпадает с исходным
 * примером ответа API из первого промпта). Сверить при первом вызове.
 */
export interface OrderItem {
  item_id: UUID;
  external_product_id: UUID;
  product_name: string;
  sku: string;
  image_url: string | null;
  item_quantity: number;
  original_unit_price: DecimalString;
  unit_price: DecimalString;
  promo_id: UUID | null;
  total_price: DecimalString;
  created_at: ISODateTime;
}

/** Заказ, как его отдаёт POST /orders, GET /orders и GET /orders/{id} (OrderRead). */
export interface OrderRead {
  order_id: UUID;
  idempotency_key: string;
  user_name: string;
  phone: string;
  email: string;
  delivery_address: string;
  total_price: DecimalString;
  status: OrderStatus;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  items: OrderItem[];
}

/** Одна позиция в теле запроса на создание заказа (OrderItemCreate). */
export interface OrderItemRequest {
  external_product_id: UUID;
  item_quantity: number;
}

/**
 * Тело POST /orders (OrderCreate). Публичный эндпоинт, без токена.
 *
 * Намеренно не содержит цен, order_id, статуса — их считает и подставляет
 * бэкенд (products_service отвечает за цены/скидки на своей стороне вызова,
 * orders_service — за сумму и статус).
 */
export interface OrderCreateRequest {
  /** Генерируется на клиенте (uuid v4) — защищает от дублей при повторной отправке. */
  idempotency_key: string;
  user_name: string;
  phone: string;
  email: string;
  delivery_address: string;
  items: OrderItemRequest[];
}

/** Тело PATCH /admin/orders/{id}/status (OrderStatusUpdate). */
export interface OrderStatusUpdateRequest {
  status: OrderStatus;
}

/** Фильтры GET /admin/orders. */
export interface AdminOrderFilters {
  status?: OrderStatus;
  email?: string;
  limit?: number;
  offset?: number;
}
