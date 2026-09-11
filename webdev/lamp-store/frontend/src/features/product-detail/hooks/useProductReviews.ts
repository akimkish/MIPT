import { useQuery } from '@tanstack/react-query';
import { getProductReviews } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { PageParams } from '../../../types/common';

/**
 * Загружает страницу опубликованных отзывов товара.
 *
 * @param productId - Идентификатор товара.
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Review>` в `data`.
 */
export function useProductReviews(productId: string, params: PageParams = {}) {
  return useQuery({
    queryKey: queryKeys.reviews.publicList(productId, params),
    queryFn: () => getProductReviews(productId, params),
    enabled: Boolean(productId),
  });
}
