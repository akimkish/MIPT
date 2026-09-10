import { useMutation } from '@tanstack/react-query';
import { createOrder } from '../../../api/ordersApi';
import { useCartStore } from '../../cart/cartStore';
import type { OrderCreateRequest } from '../../../types/order';

/**
 * Оформляет заказ и очищает корзину при успехе.
 *
 * Retry намеренно НЕ включается вручную (остаётся выключенным — дефолт
 * React Query для мутаций), хотя `idempotency_key` на бэкенде и делает
 * повтор безопасным: включать retry имеет смысл вместе с явной
 * UI-индикацией "отправляем повторно", которой пока нет. Данные о
 * заказе (номер, статус, позиции) экран подтверждения берёт напрямую
 * из ответа этой мутации — отдельного эндпоинта отслеживания заказа
 * для покупателя в проекте нет (решение: см. чат, order-status убрана).
 *
 * @returns Мутацию React Query, принимающую `OrderCreateRequest` и
 *   отдающую `OrderRead` при успехе.
 */
export function useCreateOrder() {
  const clearCart = useCartStore((state) => state.clear);

  return useMutation({
    mutationFn: (body: OrderCreateRequest) => createOrder(body),
    onSuccess: () => {
      clearCart();
    },
  });
}
