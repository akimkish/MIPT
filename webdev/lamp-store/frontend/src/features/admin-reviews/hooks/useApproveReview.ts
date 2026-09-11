import { useMutation, useQueryClient } from '@tanstack/react-query';
import { moderateReview } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Публикует отзыв (или снимает с публикации — см. `body.is_approved`).
 *
 * `productId` нужен только для точной инвалидации кэша: сам запрос
 * адресуется по `review_id`, но обновить нужно списки именно этого
 * товара — и публичный (отзыв мог опубликоваться), и админский.
 *
 * @param productId - Идентификатор товара, к которому относится отзыв.
 * @returns Мутацию React Query, принимающую `reviewId`.
 */
export function useApproveReview(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewId: string) =>
      moderateReview(reviewId, { is_approved: true }, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.publicBase(productId) });
    },
  });
}
