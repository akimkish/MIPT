import { useMutation, useQueryClient } from '@tanstack/react-query';
import { login } from '../../../api/adminApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../authStore';
import type { LoginRequest } from '../../../types/admin';

/**
 * Логинит администратора и сохраняет access-токен в `authStore`.
 *
 * @returns Мутацию React Query, принимающую `LoginRequest`.
 */
export function useAdminLogin() {
  const setToken = useAuthStore((state) => state.setToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: LoginRequest) => login(body),
    onSuccess: (data) => {
      setToken(data.access_token);
      // Сбрасываем закешированный профиль прошлой сессии (если был) —
      // иначе useCurrentAdmin может на мгновение показать чужие данные.
      queryClient.invalidateQueries({ queryKey: queryKeys.admin.me });
    },
  });
}
