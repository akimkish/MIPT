import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getAdminOrders } from '../../../api/ordersApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { AdminOrderFilters } from '../../../types/order';

/**
 * Загружает страницу заказов с фильтрами по статусу и email покупателя.
 *
 * @param filters - Фильтры и пагинация.
 * @returns Результат React Query с `Paginated<OrderRead>` в `data`.
 */
export function useAdminOrders(filters: AdminOrderFilters = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.orders.adminList(filters),
    queryFn: () => getAdminOrders(filters, token as string),
    enabled: Boolean(token),
    placeholderData: keepPreviousData,
  });
}
