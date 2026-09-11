import { useState } from 'react';
import { SOCKET_TYPE_LABELS } from '../../../lib/constants';
import { formatMoney } from '../../../lib/money';
import { useCart } from '../../cart/hooks/useCart';
import { ReviewForm } from '../components/ReviewForm';
import { ReviewList } from '../components/ReviewList';
import { useProduct } from '../hooks/useProduct';
import { useProductReviews } from '../hooks/useProductReviews';
import styles from './ProductDetailPage.module.css';

interface ProductDetailPageProps {
  productId: string;
}

/**
 * Страница товара: изображение, характеристики, цена с учётом акций,
 * добавление в корзину, отзывы и форма нового отзыва.
 *
 * `productId` передаётся пропом, а не читается из `useParams` внутри
 * компонента — страница не завязана на конкретный роутер, пока
 * `app/router.tsx` не реализован; подстановка id из URL — забота
 * вызывающего кода (когда появится роутинг).
 *
 * @param productId - Идентификатор товара.
 */
export function ProductDetailPage({ productId }: ProductDetailPageProps) {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useCart();

  const productQuery = useProduct(productId);
  const reviewsQuery = useProductReviews(productId, { limit: 20 });

  if (productQuery.isLoading) {
    return <p className={styles.status}>Загружаем товар…</p>;
  }

  if (productQuery.isError || !productQuery.data) {
    return <p className={styles.error}>Товар не найден или временно недоступен.</p>;
  }

  const product = productQuery.data;
  const outOfStock = product.quantity === 0;
  const maxQuantity = Math.max(1, product.quantity);
  const roundedRating =
    product.average_rating !== null ? Math.round(product.average_rating) : null;

  function handleAddToCart() {
    addItem(
      {
        productId: product.product_id,
        productName: product.product_name,
        sku: product.sku,
        imageUrl: product.image_url,
        unitPrice: product.display_price,
      },
      quantity,
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.layout}>
        <div className={styles.imageWrap}>
          {product.image_url ? (
            <img src={product.image_url} alt={product.product_name} className={styles.image} />
          ) : (
            <div className={styles.imagePlaceholder} aria-hidden="true">
              {SOCKET_TYPE_LABELS[product.socket_type]}
            </div>
          )}
        </div>

        <div className={styles.info}>
          <p className={styles.breadcrumb}>
            {product.category.name} · {product.manufacturer.name}
          </p>
          <h1 className={styles.title}>{product.product_name}</h1>

          {product.average_rating !== null && roundedRating !== null && (
            <p className={styles.rating} aria-label={`Средняя оценка ${product.average_rating.toFixed(1)} из 5`}>
              {'★'.repeat(roundedRating)}
              {'☆'.repeat(5 - roundedRating)}
              <span className={styles.ratingValue}>{product.average_rating.toFixed(1)}</span>
            </p>
          )}

          <dl className={styles.specs}>
            <div>
              <dt>Цоколь</dt>
              <dd>{SOCKET_TYPE_LABELS[product.socket_type]}</dd>
            </div>
            <div>
              <dt>Мощность</dt>
              <dd>{product.power_watts} Вт</dd>
            </div>
            <div>
              <dt>Цветовая температура</dt>
              <dd>{product.color_temperature_k} К</dd>
            </div>
            <div>
              <dt>Артикул</dt>
              <dd>{product.sku}</dd>
            </div>
          </dl>

          {product.description && <p className={styles.description}>{product.description}</p>}

          <div className={styles.priceBlock}>
            <span className={styles.price}>{formatMoney(product.display_price)}</span>
            {product.bulk_discount_hint && <span className={styles.hint}>{product.bulk_discount_hint}</span>}
          </div>

          {outOfStock ? (
            <p className={styles.outOfStock}>Нет в наличии</p>
          ) : (
            <div className={styles.addRow}>
              <input
                type="number"
                min={1}
                max={maxQuantity}
                value={quantity}
                onChange={(e) => setQuantity(Math.min(maxQuantity, Math.max(1, Number(e.target.value))))}
                className={styles.quantityInput}
              />
              <button type="button" className={styles.addButton} onClick={handleAddToCart}>
                В корзину
              </button>
            </div>
          )}
        </div>
      </div>

      <section className={styles.reviewsSection}>
        <h2 className={styles.reviewsHeading}>Отзывы</h2>
        {reviewsQuery.isLoading && <p className={styles.status}>Загружаем отзывы…</p>}
        {reviewsQuery.data && <ReviewList reviews={reviewsQuery.data.items} />}
        <ReviewForm productId={productId} />
      </section>
    </div>
  );
}
