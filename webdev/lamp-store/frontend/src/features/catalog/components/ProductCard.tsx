import type { MouseEvent } from 'react';
import { kelvinToRgb } from '../../../lib/colorTemperature';
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
 * Карточка товара в сетке витрины — оформлена как складская бирка:
 * перфорация (пунктир) между фото и характеристиками, "дырка для нитки"
 * в углу. Точка рядом с цветовой температурой — реальный приблизительный
 * цвет свечения лампы при этом значении К (см. `kelvinToRgb`), а не
 * декоративная точка произвольного цвета.
 *
 * "В корзину" добавляет 1 штуку сразу — количество можно поменять в
 * самой корзине. Товар без остатка (`quantity === 0`) показывает
 * подпись «Нет в наличии» вместо кнопки.
 *
 * @param product - Элемент витрины с уже посчитанной ценой по акциям.
 * @param onOpen - Колбэк перехода на страницу товара.
 */
export function ProductCard({ product, onOpen }: ProductCardProps) {
  const { addItem } = useCart();
  const outOfStock = product.quantity === 0;

  function handleAddToCart(event: MouseEvent) {
    event.stopPropagation();
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
      className={styles.tag}
      onClick={() => onOpen?.(product.product_id)}
      role={onOpen ? 'button' : undefined}
      tabIndex={onOpen ? 0 : undefined}
    >
      <span className={styles.punchHole} aria-hidden="true" />

      <div className={styles.imageWrap}>
        {product.image_url ? (
          <img src={product.image_url} alt={product.product_name} className={styles.image} />
        ) : (
          <div className={styles.imagePlaceholder} aria-hidden="true">
            {product.sku}
          </div>
        )}
      </div>

      <div className={styles.body}>
        <h3 className={styles.title}>{product.product_name}</h3>

        <div className={styles.specs}>
          <span className={styles.spec}>
            <span
              className={styles.kelvinDot}
              style={{ background: kelvinToRgb(product.color_temperature_k) }}
              aria-hidden="true"
            />
            {product.color_temperature_k} К
          </span>
          <span className={styles.spec}>{SOCKET_TYPE_LABELS[product.socket_type]}</span>
          <span className={styles.spec}>{product.power_watts} Вт</span>
        </div>

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
