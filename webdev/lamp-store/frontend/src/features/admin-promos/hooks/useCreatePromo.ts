import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createPromo } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PromoCreateRequest } from '../../../types/promo';

/**
 * Создаёт акцию на товар.
 *
 * Инвалидирует не только список акций товара, но и публичный каталог/
 * карточку товара: `display_price` и `bulk_discount_hint` на витрине
 * зависят от активных акций и должны обновиться сразу после создания.
 *
 * @returns Мутацию React Query, принимающую `PromoCreateRequest`.
 */
export function useCreatePromo() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: PromoCreateRequest) => createPromo(body, token as string),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promos.adminBase(variables.product_id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(variables.product_id) });
    },
  });
}
