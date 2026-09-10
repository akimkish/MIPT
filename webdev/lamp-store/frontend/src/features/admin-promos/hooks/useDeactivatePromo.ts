import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deactivatePromo } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Выключает акцию (физическое удаление запрещено доменной моделью).
 *
 * @param productId - Идентификатор товара акции (для инвалидации кэша витрины).
 * @returns Мутацию React Query, принимающую `promoId`.
 */
export function useDeactivatePromo(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (promoId: string) => deactivatePromo(promoId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promos.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
