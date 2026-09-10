import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteReview } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Физически удаляет отзыв (модерация спама/оскорблений — удаление разрешено доменной моделью).
 *
 * @param productId - Идентификатор товара, к которому относится отзыв (для инвалидации кэша).
 * @returns Мутацию React Query, принимающую `reviewId`.
 */
export function useDeleteReview(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewId: string) => deleteReview(reviewId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.publicBase(productId) });
    },
  });
}
