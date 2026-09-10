import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CartItem, CartState } from './types';

/**
 * Стор корзины покупателя.
 *
 * Zustand + `persist` (localStorage), а не Context API — обоснование
 * см. в проектировании структуры: точечные обновления по одной позиции
 * без ре-рендера всего дерева и персистентность в одну строку через
 * middleware вместо ручного `useEffect` с сериализацией. Аккаунтов
 * покупателей нет (known_limitations #8), поэтому корзина существует
 * только в этом браузере и не синхронизируется между устройствами —
 * это осознанное ограничение учебного проекта, не забытая фича.
 */
export const useCartStore = create<CartState>()(
  persist(
    (set) => ({
      items: [],

      addItem: (item, quantity = 1) =>
        set((state) => {
          const existing = state.items.find((i) => i.productId === item.productId);
          if (existing) {
            return {
              items: state.items.map((i) =>
                i.productId === item.productId
                  ? { ...i, quantity: i.quantity + quantity }
                  : i,
              ),
            };
          }
          return { items: [...state.items, { ...item, quantity }] };
        }),

      removeItem: (productId) =>
        set((state) => ({ items: state.items.filter((i) => i.productId !== productId) })),

      setQuantity: (productId, quantity) =>
        set((state) => {
          // quantity <= 0 трактуем как удаление позиции, а не как ошибку
          // ввода — типичный UX кнопок +/- в корзине.
          if (quantity <= 0) {
            return { items: state.items.filter((i) => i.productId !== productId) };
          }
          return {
            items: state.items.map((i) => (i.productId === productId ? { ...i, quantity } : i)),
          };
        }),

      clear: () => set({ items: [] }),
    }),
    { name: 'lamp-store-cart' },
  ),
);
