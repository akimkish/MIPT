import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { ProductCreateRequest } from '../../../types/product';

/**
 * Создаёт товар.
 *
 * @returns Мутацию React Query, принимающую `ProductCreateRequest`.
 */
export function useCreateProduct() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ProductCreateRequest) => createProduct(body, token as string),
    onSuccess: () => {
      // Новый товар должен появиться и в админском списке, и (если
      // is_active по умолчанию true) на витрине — инвалидируем оба.
      queryClient.invalidateQueries({ queryKey: queryKeys.products.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
    },
  });
}
