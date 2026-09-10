import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getAdminProducts } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PageParams } from '../../../types/common';

/**
 * Загружает страницу товаров для админки (включая is_active === false).
 *
 * ВАЖНО: у `GET /admin/products` нет фильтров по категории/производителю/
 * цене — только пагинация. Фильтрация в UI админки, если понадобится,
 * делается на фронте по уже полученной странице.
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<ProductRead>` в `data`.
 */
export function useAdminProducts(params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.products.adminList(params),
    queryFn: () => getAdminProducts(params, token as string),
    enabled: Boolean(token),
    placeholderData: keepPreviousData,
  });
}
