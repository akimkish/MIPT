import { useQuery } from '@tanstack/react-query';
import { getProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';

/**
 * Загружает полную карточку товара для страницы товара.
 *
 * @param productId - Идентификатор товара (например, из `useParams`).
 * @returns Результат React Query с `ProductDetail` в `data`.
 */
export function useProduct(productId: string) {
  return useQuery({
    queryKey: queryKeys.products.detail(productId),
    queryFn: () => getProduct(productId),
    enabled: Boolean(productId), // не запускать запрос до появления id
  });
}
