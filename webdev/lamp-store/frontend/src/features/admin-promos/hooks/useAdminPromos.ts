import { useQuery } from '@tanstack/react-query';
import { getAdminPromos } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { AdminPromoFilters } from '../../../types/promo';

/**
 * Загружает страницу всех акций товара (включая выключенные).
 *
 * `filters.product_id` обязателен — общего списка акций по всем товарам
 * сразу бэкенд не отдаёт. Экран должен сперва предложить выбрать товар.
 *
 * @param filters - Фильтр по товару и пагинация.
 * @returns Результат React Query с `Paginated<Promo>` в `data`.
 */
export function useAdminPromos(filters: AdminPromoFilters) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.promos.adminList(filters),
    queryFn: () => getAdminPromos(filters, token as string),
    enabled: Boolean(token) && Boolean(filters.product_id),
  });
}
