import { useQuery } from '@tanstack/react-query';
import { getMe } from '../../../api/adminApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../authStore';

/**
 * Загружает профиль текущего администратора через `GET /auth/me`.
 *
 * `enabled` завязан на наличие токена: без него бэкенд всё равно ответит
 * 401, но нет смысла делать заведомо провальный запрос до логина.
 *
 * @returns Результат React Query с `AdminRead` в `data`.
 */
export function useCurrentAdmin() {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.admin.me,
    queryFn: () => getMe(token as string),
    enabled: Boolean(token),
    staleTime: 5 * 60 * 1000,
  });
}
