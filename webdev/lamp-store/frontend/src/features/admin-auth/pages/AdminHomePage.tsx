import { ROLE_LABELS } from '../../../lib/constants';
import { useCurrentAdmin } from '../hooks/useCurrentAdmin';
import styles from './AdminHomePage.module.css';

/**
 * Временная домашняя страница админки: профиль вошедшего администратора
 * и список разделов, которые появятся по мере реализации.
 *
 * Единственный экран, доступный сразу после логина, пока
 * admin-products/admin-reviews/admin-promos/admin-orders/
 * admin-catalog-refs/admin-management не построены как страницы —
 * их React Query хуки уже готовы, UI ещё нет.
 *
 * Рендерится только внутри `RequireAdmin`, поэтому `currentAdmin.data`
 * на этот момент гарантированно загружен — ранний `return null`
 * подстраховывает только на случай доли секунды между рендерами.
 */
export function AdminHomePage() {
  const currentAdmin = useCurrentAdmin();

  if (!currentAdmin.data) return null;

  const admin = currentAdmin.data;

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Добро пожаловать, {admin.full_name}</h1>
      <p className={styles.role}>Роль: {ROLE_LABELS[admin.role_name]}</p>

      <ul className={styles.sections}>
        <li>Товары — скоро</li>
        <li>Категории и производители — скоро</li>
        <li>Модерация отзывов — скоро</li>
        <li>Промо-акции — скоро</li>
        <li>Заказы — скоро</li>
        {admin.role_name === 'superadmin' && <li>Управление администраторами — скоро</li>}
      </ul>
    </div>
  );
}
