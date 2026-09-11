import { Link, Outlet } from 'react-router-dom';
import { useAuthStore } from '../features/admin-auth/authStore';
import { useCurrentAdmin } from '../features/admin-auth/hooks/useCurrentAdmin';
import { ROLE_LABELS } from '../lib/constants';
import styles from './AdminLayout.module.css';

/**
 * Общий каркас защищённых `/admin/*` страниц: тонкая шапка с email/ролью
 * администратора и выходом, дальше — конкретная страница раздела.
 *
 * Рендерится только внутри `RequireAdmin` — можно рассчитывать, что
 * `useCurrentAdmin()` уже успешно отработал; вызов здесь переиспользует
 * тот же кэш React Query, повторного запроса на сервер не будет.
 *
 * "Выйти" зовёт `clearToken()` и ничего не делает с навигацией явно —
 * как только токен обнулится, `RequireAdmin` сам увидит его отсутствие
 * на следующем рендере и отправит на `/admin/login`.
 */
export function AdminLayout() {
  const currentAdmin = useCurrentAdmin();
  const clearToken = useAuthStore((state) => state.clearToken);

  return (
    <div className={styles.shell}>
      <header className={styles.bar}>
        <Link to="/admin" className={styles.brand}>
          Lamp Store · Админка
        </Link>
        <div className={styles.session}>
          {currentAdmin.data && (
            <span className={styles.who}>
              {currentAdmin.data.email} · {ROLE_LABELS[currentAdmin.data.role_name]}
            </span>
          )}
          <button type="button" className={styles.logout} onClick={clearToken}>
            Выйти
          </button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
