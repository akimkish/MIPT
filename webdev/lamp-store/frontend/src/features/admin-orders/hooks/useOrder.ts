import { useQuery } from '@tanstack/react-query';
import { getOrder } from '../../../api/ordersApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Загружает детали одного заказа для админки.
 *
 * `GET /orders/{id}` требует прав MANAGE_ORDERS — публичного
 * использования у этого хука нет (решение по order-status: покупатель
 * заказ по ссылке не отслеживает, см. чат).
 *
 * @param orderId - Идентификатор заказа.
 * @returns Результат React Query с `OrderRead` в `data`.
 */
export function useOrder(orderId: string) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.orders.detail(orderId),
    queryFn: () => getOrder(orderId, token as string),
    enabled: Boolean(token) && Boolean(orderId),
  });
}
