import { formatMoney } from '../../../lib/money';
import type { CartItem } from '../types';
import styles from './CartItemRow.module.css';

interface CartItemRowProps {
  item: CartItem;
  onQuantityChange: (quantity: number) => void;
  onRemove: () => void;
}

/**
 * Одна позиция в списке корзины.
 *
 * Сумма по строке (`unitPrice * quantity`) считается на клиенте только
 * для отображения — это оценка по цене на момент добавления в корзину,
 * не окончательная сумма: актуальную цену, скидки и наличие бэкенд
 * пересчитает заново при оформлении заказа (см. `useCreateOrder`).
 *
 * Уменьшение количества кнопкой "−" остановлено на 1 (кнопка
 * дизейблится), а не сворачивается в удаление позиции — явное удаление
 * через отдельную ссылку "Удалить" предсказуемее для пользователя, чем
 * случайное исчезновение товара от одного лишнего клика по степперу.
 *
 * @param item - Позиция корзины.
 * @param onQuantityChange - Вызывается с новым количеством (всегда >= 1).
 * @param onRemove - Вызывается при явном удалении позиции.
 */
export function CartItemRow({ item, onQuantityChange, onRemove }: CartItemRowProps) {
  const lineTotal = (Number(item.unitPrice) * item.quantity).toFixed(2);

  return (
    <li className={styles.row}>
      <div className={styles.imageWrap}>
        {item.imageUrl ? (
          <img src={item.imageUrl} alt={item.productName} className={styles.image} />
        ) : (
          <div className={styles.imagePlaceholder} aria-hidden="true">
            {item.sku}
          </div>
        )}
      </div>

      <div className={styles.info}>
        <p className={styles.name}>{item.productName}</p>
        <p className={styles.sku}>{item.sku}</p>
        <p className={styles.unitPrice}>{formatMoney(item.unitPrice)} / шт.</p>
      </div>

      <div className={styles.quantity}>
        <button
          type="button"
          className={styles.quantityButton}
          disabled={item.quantity <= 1}
          onClick={() => onQuantityChange(item.quantity - 1)}
          aria-label="Уменьшить количество"
        >
          −
        </button>
        <span className={styles.quantityValue}>{item.quantity}</span>
        <button
          type="button"
          className={styles.quantityButton}
          onClick={() => onQuantityChange(item.quantity + 1)}
          aria-label="Увеличить количество"
        >
          +
        </button>
      </div>

      <div className={styles.lineTotal}>{formatMoney(lineTotal)}</div>

      <button type="button" className={styles.removeButton} onClick={onRemove}>
        Удалить
      </button>
    </li>
  );
}
