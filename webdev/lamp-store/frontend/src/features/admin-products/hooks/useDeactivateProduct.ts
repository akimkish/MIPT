import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deactivateProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Снимает товар с витрины (физическое удаление запрещено доменной моделью).
 *
 * @returns Мутацию React Query, принимающую `productId`.
 */
export function useDeactivateProduct() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (productId: string) => deactivateProduct(productId, token as string),
    onSuccess: (_data, productId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
