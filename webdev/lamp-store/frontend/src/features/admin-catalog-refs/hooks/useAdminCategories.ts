import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createCategory,
  deactivateCategory,
  getAdminCategories,
  updateCategory,
} from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { CategoryCreateRequest, CategoryUpdateRequest } from '../../../types/category';
import type { PageParams } from '../../../types/common';

/**
 * Загружает страницу всех категорий для админки (включая скрытые).
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Category>` в `data`.
 */
export function useAdminCategories(params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.categories.adminList(params),
    queryFn: () => getAdminCategories(params, token as string),
    enabled: Boolean(token),
  });
}

/**
 * Создаёт категорию.
 *
 * @returns Мутацию React Query, принимающую `CategoryCreateRequest`.
 */
export function useCreateCategory() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CategoryCreateRequest) => createCategory(body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.adminBase });
    },
  });
}

/**
 * Частично обновляет категорию.
 *
 * @param categoryId - Идентификатор категории.
 * @returns Мутацию React Query, принимающую `CategoryUpdateRequest`.
 */
export function useUpdateCategory(categoryId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CategoryUpdateRequest) => updateCategory(categoryId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.adminBase });
    },
  });
}

/**
 * Скрывает категорию с витрины (физическое удаление запрещено, ON DELETE RESTRICT).
 *
 * @returns Мутацию React Query, принимающую `categoryId`.
 */
export function useDeactivateCategory() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (categoryId: string) => deactivateCategory(categoryId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.adminBase });
    },
  });
}
