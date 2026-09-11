import { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../authStore';
import { useCurrentAdmin } from '../hooks/useCurrentAdmin';

/**
 * Guard для защищённых `/admin/*` маршрутов.
 *
 * Проверка в два слоя: без токена в сторе — сразу редирект на логин, без
 * обращения к серверу. С токеном — дополнительно проверяем его валидность
 * через `GET /auth/me` (`useCurrentAdmin`): если токен просрочен, испорчен
 * или админ деактивирован (доступ по уже выданному токену сохраняется до
 * истечения его TTL — see known_limitations #3 — но не дольше), сервер
 * ответит 401. В этом случае явно разлогиниваем на клиенте и уводим на
 * логин, а не оставляем администратора один на один с зависшим экраном.
 *
 * Сброс токена (`clearToken`) сделан в `useEffect`, а не прямо в теле
 * рендера — вызывать действие стора (эквивалент `setState`) во время
 * рендера запрещено правилами React и может дать лишний повторный рендер
 * в StrictMode.
 */
export function RequireAdmin() {
  const token = useAuthStore((state) => state.token);
  const clearToken = useAuthStore((state) => state.clearToken);
  const currentAdmin = useCurrentAdmin();

  useEffect(() => {
    if (currentAdmin.isError) {
      clearToken();
    }
  }, [currentAdmin.isError, clearToken]);

  if (!token) {
    return <Navigate to="/admin/login" replace />;
  }

  if (currentAdmin.isLoading) {
    return <p style={{ padding: 'var(--space-8)', textAlign: 'center' }}>Проверяем доступ…</p>;
  }

  if (currentAdmin.isError) {
    return <Navigate to="/admin/login" replace />;
  }

  return <Outlet />;
}
