import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updatePromo } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PromoUpdateRequest } from '../../../types/promo';

/**
 * Частично обновляет акцию. `product_id` в теле передавать нельзя —
 * см. `PromoUpdateRequest` — перепривязать акцию к другому товару нельзя.
 *
 * @param productId - Идентификатор товара акции (для инвалидации кэша витрины).
 * @returns Мутацию React Query, принимающую `{ promoId, body }`.
 */
export function useUpdatePromo(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ promoId, body }: { promoId: string; body: PromoUpdateRequest }) =>
      updatePromo(promoId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promos.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
