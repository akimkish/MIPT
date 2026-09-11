import { formatMoney } from '../../../lib/money';
import { CartItemRow } from '../components/CartItemRow';
import { useCart } from '../hooks/useCart';
import styles from './CartPage.module.css';

interface CartPageProps {
  onContinueShopping: () => void;
  onCheckout: () => void;
}

/**
 * Страница корзины: список позиций, изменение количества, удаление,
 * промежуточная сумма и переход к оформлению заказа.
 *
 * `onContinueShopping`/`onCheckout` — колбэки навигации, а не прямой
 * вызов `useNavigate` внутри страницы: тот же принцип, что и у
 * `CatalogPage`/`ProductDetailPage` — страница не завязана на роутер,
 * обёртку делает `CartRoute` в `app/router.tsx`.
 *
 * Промежуточная сумма считается на клиенте по ценам на момент
 * добавления в корзину — это оценка, не окончательная сумма заказа.
 * Актуальные цены, скидки и наличие пересчитает бэкенд при оформлении
 * (см. `useCreateOrder`), поэтому итог здесь помечен как промежуточный.
 *
 * @param onContinueShopping - Вызывается при клике "Продолжить покупки".
 * @param onCheckout - Вызывается при клике "Оформить заказ".
 */
export function CartPage({ onContinueShopping, onCheckout }: CartPageProps) {
  const { items, totalQuantity, setQuantity, removeItem } = useCart();

  const subtotal = items
    .reduce((sum, item) => sum + Number(item.unitPrice) * item.quantity, 0)
    .toFixed(2);

  if (items.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.empty}>
          <h1 className={styles.emptyHeading}>Корзина пуста</h1>
          <p className={styles.emptyText}>Загляните в каталог — там наверняка найдётся подходящая лампа.</p>
          <button type="button" className={styles.continueButton} onClick={onContinueShopping}>
            В каталог
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.heading}>Корзина</h1>
          <p className={styles.subheading}>{totalQuantity} товаров</p>
        </div>
      </header>

      <div className={styles.content}>
        <ul className={styles.list}>
          {items.map((item) => (
            <CartItemRow
              key={item.productId}
              item={item}
              onQuantityChange={(quantity) => setQuantity(item.productId, quantity)}
              onRemove={() => removeItem(item.productId)}
            />
          ))}
        </ul>

        <div className={styles.summary}>
          <div className={styles.subtotalRow}>
            <span className={styles.subtotalLabel}>Промежуточная сумма</span>
            <span className={styles.subtotalValue}>{formatMoney(subtotal)}</span>
          </div>
          <p className={styles.note}>Точную сумму с учётом акций и наличия покажем на следующем шаге.</p>

          <div className={styles.actions}>
            <button type="button" className={styles.continueLink} onClick={onContinueShopping}>
              Продолжить покупки
            </button>
            <button type="button" className={styles.checkoutButton} onClick={onCheckout}>
              Оформить заказ
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
