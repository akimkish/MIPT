import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createReview } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { ReviewCreateRequest } from '../../../types/review';

/**
 * Отправляет отзыв на товар (без аутентификации — аккаунтов покупателей нет).
 *
 * Инвалидирует публичный список отзывов, хотя новый отзыв не появится в
 * нём сразу: он уходит на модерацию (`is_approved=false`). Инвалидация —
 * задел на будущее (когда отзыв одобрят), а не ошибка ожидания.
 *
 * @param productId - Идентификатор товара, на который оставляют отзыв.
 * @returns Мутацию React Query, принимающую `ReviewCreateRequest`.
 */
export function useCreateReview(productId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ReviewCreateRequest) => createReview(productId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.publicBase(productId) });
    },
  });
}
