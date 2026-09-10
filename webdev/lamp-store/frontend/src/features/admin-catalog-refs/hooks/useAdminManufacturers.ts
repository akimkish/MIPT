import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createManufacturer,
  deactivateManufacturer,
  getAdminManufacturers,
  updateManufacturer,
} from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PageParams } from '../../../types/common';
import type {
  ManufacturerCreateRequest,
  ManufacturerUpdateRequest,
} from '../../../types/manufacturer';

/**
 * Загружает страницу всех производителей для админки (включая скрытых).
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Manufacturer>` в `data`.
 */
export function useAdminManufacturers(params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.manufacturers.adminList(params),
    queryFn: () => getAdminManufacturers(params, token as string),
    enabled: Boolean(token),
  });
}

/**
 * Создаёт производителя.
 *
 * @returns Мутацию React Query, принимающую `ManufacturerCreateRequest`.
 */
export function useCreateManufacturer() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ManufacturerCreateRequest) => createManufacturer(body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.manufacturers.adminBase });
    },
  });
}

/**
 * Частично обновляет производителя.
 *
 * @param manufacturerId - Идентификатор производителя.
 * @returns Мутацию React Query, принимающую `ManufacturerUpdateRequest`.
 */
export function useUpdateManufacturer(manufacturerId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ManufacturerUpdateRequest) =>
      updateManufacturer(manufacturerId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.manufacturers.adminBase });
    },
  });
}

/**
 * Скрывает производителя с витрины (физическое удаление запрещено).
 *
 * @returns Мутацию React Query, принимающую `manufacturerId`.
 */
export function useDeactivateManufacturer() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (manufacturerId: string) => deactivateManufacturer(manufacturerId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.manufacturers.adminBase });
    },
  });
}
