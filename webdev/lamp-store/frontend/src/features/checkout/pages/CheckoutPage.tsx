import { useState } from 'react';
import type { FormEvent } from 'react';
import { ORDER_STATUS_LABELS } from '../../../lib/constants';
import { formatMoney } from '../../../lib/money';
import type { OrderRead } from '../../../types/order';
import { useCart } from '../../cart/hooks/useCart';
import { useCreateOrder } from '../hooks/useCreateOrder';
import styles from './CheckoutPage.module.css';

interface CheckoutPageProps {
  onContinueShopping: () => void;
}

/**
 * Страница оформления заказа: форма контактных данных + сводка корзины,
 * и, после успешной отправки, экран подтверждения на основе ответа
 * сервера (`OrderRead`).
 *
 * Подтверждение строится ИСКЛЮЧИТЕЛЬНО из ответа `POST /orders`, без
 * отдельного запроса за деталями заказа — публичного `GET /orders/{id}`
 * для покупателя в бэкенде нет (решение зафиксировано ранее: см. историю
 * чата про order-status). Это единственный момент, когда покупатель
 * вообще видит данные своего заказа — если он потеряет эту страницу
 * (обновит её), вернуться к заказу он не сможет.
 *
 * `idempotency_key` генерируется один раз при монтировании страницы
 * (`useState(() => crypto.randomUUID())`) и переиспользуется при всех
 * попытках отправки формы, пока страница не перезагружена — это и есть
 * защита от дублей при повторной отправке (см. `useCreateOrder`).
 *
 * @param onContinueShopping - Колбэк навигации на витрину — вызывается
 *   и с экрана подтверждения, и из пустой корзины. Страница, как и
 *   `CartPage`/`CatalogPage`, не завязана на роутер напрямую.
 */
export function CheckoutPage({ onContinueShopping }: CheckoutPageProps) {
  const { items, toOrderItems } = useCart();
  const createOrder = useCreateOrder();

  const [idempotencyKey] = useState(() => crypto.randomUUID());
  const [userName, setUserName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [confirmedOrder, setConfirmedOrder] = useState<OrderRead | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createOrder.mutate(
      {
        idempotency_key: idempotencyKey,
        user_name: userName,
        phone,
        email,
        delivery_address: deliveryAddress,
        items: toOrderItems(),
      },
      { onSuccess: (order) => setConfirmedOrder(order) },
    );
  }

  if (confirmedOrder) {
    return (
      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.headerInner}>
            <h1 className={styles.heading}>Заказ оформлен</h1>
            <p className={styles.subheading}>№ {confirmedOrder.order_id}</p>
          </div>
        </header>

        <div className={styles.content}>
          <p className={styles.confirmText}>
            Статус: {ORDER_STATUS_LABELS[confirmedOrder.status]}. Мы свяжемся по адресу {confirmedOrder.email}.
          </p>

          <div className={styles.summary}>
            <ul className={styles.summaryList}>
              {confirmedOrder.items.map((item) => (
                <li key={item.item_id} className={styles.summaryRow}>
                  <span className={styles.summaryName}>
                    {item.product_name} × {item.item_quantity}
                  </span>
                  <span className={styles.summaryPrice}>{formatMoney(item.total_price)}</span>
                </li>
              ))}
            </ul>
            <div className={styles.totalRow}>
              <span>Итого</span>
              <span className={styles.totalValue}>{formatMoney(confirmedOrder.total_price)}</span>
            </div>
          </div>

          <div className={styles.confirmActions}>
            <button type="button" className={styles.continueButton} onClick={onContinueShopping}>
              Продолжить покупки
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.empty}>
          <h1 className={styles.emptyHeading}>Корзина пуста</h1>
          <p className={styles.emptyText}>Оформить заказ можно, когда в корзине есть хотя бы один товар.</p>
          <button type="button" className={styles.continueButton} onClick={onContinueShopping}>
            В каталог
          </button>
        </div>
      </div>
    );
  }

  const estimatedTotal = items.reduce((sum, item) => sum + Number(item.unitPrice) * item.quantity, 0).toFixed(2);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.heading}>Оформление заказа</h1>
          <p className={styles.subheading}>{items.length} товаров в корзине</p>
        </div>
      </header>

      <div className={styles.content}>
        <div className={styles.layout}>
          <form className={styles.form} onSubmit={handleSubmit}>
            <label className={styles.field}>
              Имя
              <input
                type="text"
                required
                minLength={1}
                maxLength={100}
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </label>

            <label className={styles.field}>
              Телефон
              <input
                type="tel"
                required
                minLength={1}
                maxLength={20}
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </label>

            <label className={styles.field}>
              Email
              <input type="email" required maxLength={255} value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>

            <label className={styles.field}>
              Адрес доставки
              <textarea
                required
                minLength={1}
                maxLength={500}
                rows={3}
                value={deliveryAddress}
                onChange={(e) => setDeliveryAddress(e.target.value)}
              />
            </label>

            {createOrder.isError && <p className={styles.error}>{createOrder.error.message}</p>}

            <button type="submit" className={styles.submitButton} disabled={createOrder.isPending}>
              {createOrder.isPending ? 'Оформляем…' : 'Подтвердить заказ'}
            </button>
          </form>

          <aside className={styles.summary}>
            <h2 className={styles.summaryHeading}>Ваш заказ</h2>
            <ul className={styles.summaryList}>
              {items.map((item) => (
                <li key={item.productId} className={styles.summaryRow}>
                  <span className={styles.summaryName}>
                    {item.productName} × {item.quantity}
                  </span>
                  <span className={styles.summaryPrice}>
                    {formatMoney((Number(item.unitPrice) * item.quantity).toFixed(2))}
                  </span>
                </li>
              ))}
            </ul>
            <div className={styles.totalRow}>
              <span>Промежуточный итог</span>
              <span className={styles.totalValue}>{formatMoney(estimatedTotal)}</span>
            </div>
            <p className={styles.note}>Точную сумму подтвердит сервер после проверки акций и наличия.</p>
          </aside>
        </div>
      </div>
    </div>
  );
}
