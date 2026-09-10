import type { DecimalString, UUID } from '../../types/common';

/**
 * Позиция корзины на клиенте.
 *
 * Хранит копию нужных для отображения полей карточки товара на момент
 * добавления (название, картинка, цена), а не ссылку на весь
 * `ProductCatalogItem` — так корзина не ломается, если товар потом
 * изменится или будет снят с продажи. Актуальность цены и наличие всё
 * равно пересчитывает и проверяет бэкенд в момент оформления заказа.
 */
export interface CartItem {
  productId: UUID;
  productName: string;
  sku: string;
  imageUrl: string | null;
  /** Цена за единицу на момент добавления — только для отображения в корзине. */
  unitPrice: DecimalString;
  quantity: number;
}

/** Форма Zustand-стора корзины. */
export interface CartState {
  items: CartItem[];
  addItem: (item: Omit<CartItem, 'quantity'>, quantity?: number) => void;
  removeItem: (productId: UUID) => void;
  setQuantity: (productId: UUID, quantity: number) => void;
  clear: () => void;
}
