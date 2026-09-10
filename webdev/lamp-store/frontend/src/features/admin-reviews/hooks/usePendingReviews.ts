import { useQuery } from '@tanstack/react-query';
import { getAdminReviewsForProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PageParams } from '../../../types/common';

/**
 * Загружает все отзывы товара для модерации (включая неопубликованные).
 *
 * Имя файла унаследовано от структуры первого шага проектирования, но
 * бэкенд не отдаёт список "все отзывы на модерации сразу по всем
 * товарам" — `product_id` обязателен в `GET /admin/reviews`. Поэтому
 * хук принимает `productId`: экран модерации должен сначала предложить
 * выбрать товар (например, из списка `useAdminProducts`).
 *
 * @param productId - Идентификатор товара.
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Review>` в `data`.
 */
export function usePendingReviews(productId: string, params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.reviews.adminList(productId, params),
    queryFn: () => getAdminReviewsForProduct(productId, params, token as string),
    enabled: Boolean(token) && Boolean(productId),
  });
}
