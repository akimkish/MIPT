import { Link } from 'react-router-dom';
import { useCart } from '../features/cart/hooks/useCart';
import styles from './AppHeader.module.css';

/**
 * Постоянная тонкая шапка поверх всех страниц — бренд-ссылка на каталог
 * и переход в корзину со счётчиком товаров.
 *
 * Появилась именно в этом шаге не случайно: до неё страница `/cart`
 * была бы физически доступна только по прямому вводу URL — нигде в
 * интерфейсе не было ссылки на неё вообще.
 *
 * Оформлена светлой и тонкой намеренно — в отличие от тёмных "панелей
 * управления" `CatalogPage`/`CartPage`, эта шапка постоянная и не
 * должна с ними конкурировать за внимание.
 */
export function AppHeader() {
  const { totalQuantity } = useCart();

  return (
    <div className={styles.bar}>
      <Link to="/" className={styles.brand}>
        Lamp Store
      </Link>
      <Link to="/cart" className={styles.cartLink}>
        Корзина
        {totalQuantity > 0 && <span className={styles.badge}>{totalQuantity}</span>}
      </Link>
    </div>
  );
}
