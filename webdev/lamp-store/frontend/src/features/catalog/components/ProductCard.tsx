import type { MouseEvent } from 'react';
import { SOCKET_TYPE_LABELS } from '../../../lib/constants';
import { formatMoney } from '../../../lib/money';
import type { ProductCatalogItem } from '../../../types/product';
import { useCart } from '../../cart/hooks/useCart';
import styles from './ProductCard.module.css';

interface ProductCardProps {
  product: ProductCatalogItem;
  /** Открыть карточку товара. Необязателен: без него карточка не кликабельна. */
  onOpen?: (productId: string) => void;
}

/**
 * Карточка товара в сетке витрины.
 *
 * "В корзину" добавляет 1 штуку сразу, без диалога выбора количества —
 * количество можно изменить прямо в корзине. Товар без остатка
 * (`quantity === 0`) показывает подпись "Нет в наличии" вместо кнопки:
 * снятый с продажи (`is_active=false`) товар витрина вообще не покажет,
 * а вот видимый товар с нулевым остатком — обычная ситуация (раскупили,
 * админ ещё не деактивировал), это разные вещи.
 *
 * @param product - Элемент витрины с уже посчитанной ценой по акциям.
 * @param onOpen - Колбэк перехода на страницу товара.
 */
export function ProductCard({ product, onOpen }: ProductCardProps) {
  const { addItem } = useCart();
  const outOfStock = product.quantity === 0;

  function handleAddToCart(event: MouseEvent) {
    event.stopPropagation(); // не открывать карточку товара кликом по кнопке
    addItem({
      productId: product.product_id,
      productName: product.product_name,
      sku: product.sku,
      imageUrl: product.image_url,
      unitPrice: product.display_price,
    });
  }

  return (
    <article
      className={styles.card}
      onClick={() => onOpen?.(product.product_id)}
      role={onOpen ? 'button' : undefined}
      tabIndex={onOpen ? 0 : undefined}
    >
      <div className={styles.imageWrap}>
        {product.image_url ? (
          <img src={product.image_url} alt={product.product_name} className={styles.image} />
        ) : (
          <div className={styles.imagePlaceholder} aria-hidden="true">
            {SOCKET_TYPE_LABELS[product.socket_type]}
          </div>
        )}
      </div>

      <div className={styles.body}>
        <h3 className={styles.title}>{product.product_name}</h3>
        <p className={styles.meta}>
          {SOCKET_TYPE_LABELS[product.socket_type]} · {product.power_watts} Вт ·{' '}
          {product.color_temperature_k} К
        </p>

        <div className={styles.priceRow}>
          <span className={styles.price}>{formatMoney(product.display_price)}</span>
          {product.bulk_discount_hint && <span className={styles.hint}>{product.bulk_discount_hint}</span>}
        </div>

        <button type="button" className={styles.addButton} disabled={outOfStock} onClick={handleAddToCart}>
          {outOfStock ? 'Нет в наличии' : 'В корзину'}
        </button>
      </div>
    </article>
  );
}
