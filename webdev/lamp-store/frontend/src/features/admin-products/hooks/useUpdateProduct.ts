import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { ProductUpdateRequest } from '../../../types/product';

/**
 * Частично обновляет товар. `quantity` в теле передавать нельзя —
 * см. `ProductUpdateRequest` — остаток этим методом не меняется.
 *
 * @param productId - Идентификатор обновляемого товара.
 * @returns Мутацию React Query, принимающую `ProductUpdateRequest`.
 */
export function useUpdateProduct(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ProductUpdateRequest) => updateProduct(productId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
