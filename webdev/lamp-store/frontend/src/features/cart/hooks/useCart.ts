import { useCartStore } from '../cartStore';
import type { OrderItemRequest } from '../../../types/order';

/**
 * Тонкая обёртка над `cartStore` для использования в компонентах.
 *
 * Не заводит нового состояния — только читает стор и добавляет
 * производные значения (`totalQuantity`, `toOrderItems`), которые иначе
 * пришлось бы пересчитывать в каждом компоненте отдельно.
 *
 * @returns Содержимое корзины, действия над ней и хелпер для оформления заказа.
 */
export function useCart() {
  const items = useCartStore((state) => state.items);
  const addItem = useCartStore((state) => state.addItem);
  const removeItem = useCartStore((state) => state.removeItem);
  const setQuantity = useCartStore((state) => state.setQuantity);
  const clear = useCartStore((state) => state.clear);

  const totalQuantity = items.reduce((sum, item) => sum + item.quantity, 0);

  /**
   * Приводит корзину к форме, которую ждёт `OrderCreateRequest.items`.
   *
   * @returns Список позиций без цен — цену на своей стороне считает бэкенд.
   */
  function toOrderItems(): OrderItemRequest[] {
    return items.map((item) => ({
      external_product_id: item.productId,
      item_quantity: item.quantity,
    }));
  }

  return { items, totalQuantity, addItem, removeItem, setQuantity, clear, toOrderItems };
}
