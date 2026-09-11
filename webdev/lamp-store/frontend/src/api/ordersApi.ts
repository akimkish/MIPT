import type { AdminOrderFilters, OrderCreateRequest, OrderRead } from '../types/order';
import type { Paginated } from '../types/common';
import type { OrderStatus } from '../types/enums';
import { createHttpClient } from './httpClient';

const client = createHttpClient(import.meta.env.VITE_ORDERS_API_URL);

/**
 * Оформляет заказ. Единственный публичный эндпоинт этого сервиса —
 * учётных записей у покупателей нет, аутентификация не требуется.
 *
 * При 409 (дубль/нехватка остатка/товар снят с продажи) и 503
 * (products_service недоступен) бэкенд кладёт структурированную ошибку
 * `{code, message, details}` в `detail` — см. ApiError в errors.ts.
 */
export function createOrder(body: OrderCreateRequest): Promise<OrderRead> {
  return client.post<OrderRead>('/api/v1/orders', body);
}

// --- Админка: заказы (требуют JWT) --------------------------------------------

/**
 * ВАЖНО: `GET /orders/{id}` тоже требует прав MANAGE_ORDERS — публичного
 * эндпоинта "посмотреть свой заказ по ссылке" в бэкенде НЕТ. Единственный
 * источник данных о заказе для покупателя — ответ на `createOrder` в
 * момент оформления. Экран отдельного отслеживания заказа по id для
 * незалогиненного покупателя на данный момент не реализуем без изменений
 * на бэкенде — уточнить, нужен ли отдельный публичный эндпоинт.
 */
export function getOrder(orderId: string, token: string): Promise<OrderRead> {
  return client.get<OrderRead>(`/api/v1/orders/${orderId}`, { token });
}

export function getAdminOrders(
  filters: AdminOrderFilters,
  token: string,
): Promise<Paginated<OrderRead>> {
  return client.get<Paginated<OrderRead>>('/api/v1/orders', { searchParams: filters, token });
}

/** Оплаты нет — статус paid/shipped/completed проставляет админ вручную. */
export function updateOrderStatus(
  orderId: string,
  status: OrderStatus,
  token: string,
): Promise<OrderRead> {
  return client.patch<OrderRead>(`/api/v1/orders/${orderId}/status`, { status }, { token });
}
