import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateOrderStatus } from '../../../api/ordersApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { OrderStatus } from '../../../types/enums';

/**
 * Переводит заказ в новый статус. Допустимость перехода (например,
 * `paid` → `shipped`, но не `shipped` → `new`) проверяет бэкенд —
 * хук отправляет статус как есть, без собственной валидации переходов.
 *
 * @param orderId - Идентификатор заказа.
 * @returns Мутацию React Query, принимающую новый `OrderStatus`.
 */
export function useUpdateOrderStatus(orderId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (status: OrderStatus) => updateOrderStatus(orderId, status, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.orders.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.orders.detail(orderId) });
    },
  });
}
