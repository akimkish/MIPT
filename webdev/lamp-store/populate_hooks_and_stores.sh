#!/usr/bin/env bash
#
# Наполняет содержимым хуки React Query и Zustand-сторы для всех фич,
# КРОМЕ admin-management (эта фича ждёт присылки admins.py — см. чат).
#
# Запускать ПОСЛЕ create_frontend_structure.sh и populate_api_and_types.sh,
# ИЗ КОРНЯ РЕПОЗИТОРИЯ:
#
#   ./populate_hooks_and_stores.sh
#
# Идемпотентен: каждый `cat > file` полностью перезаписывает файл.
#
# Требует в package.json: @tanstack/react-query (v5, используется API
# `placeholderData: keepPreviousData`) и zustand. Установка пакетов
# не входит в этот скрипт — только код.

set -euo pipefail

if [[ ! -d "frontend/src" ]]; then
  echo "Ошибка: 'frontend/src' не найдена." >&2
  echo "Сначала запустите create_frontend_structure.sh и populate_api_and_types.sh," >&2
  echo "затем этот скрипт — из корня репозитория lamp-store/." >&2
  exit 1
fi

SRC="frontend/src"

# ============================================================================
# lib/queryKeys.ts
# ============================================================================
cat > "$SRC/lib/queryKeys.ts" << 'EOF'
import type { PageParams } from '../types/common';
import type { AdminOrderFilters } from '../types/order';
import type { AdminPromoFilters } from '../types/promo';
import type { ProductFilters } from '../types/product';

/**
 * Централизованные ключи React Query.
 *
 * Для ресурсов с мутациями (create/update/deactivate) заведён отдельный
 * "base"-ключ без параметров запроса — по нему `invalidateQueries` матчит
 * все варианты списка сразу (React Query сравнивает ключи по префиксу
 * массива), не нужно перечислять все возможные фильтры и страницы.
 * Простой объект с функциями выбран вместо отдельной библиотеки
 * query-key-factory — для количества ресурсов этого проекта библиотека
 * не окупает себя лишней зависимостью.
 */
export const queryKeys = {
  categories: {
    publicList: (params: PageParams = {}) => ['categories', 'public', params] as const,
    adminBase: ['categories', 'admin'] as const,
    adminList: (params: PageParams = {}) => ['categories', 'admin', params] as const,
  },
  manufacturers: {
    publicList: (params: PageParams = {}) => ['manufacturers', 'public', params] as const,
    adminBase: ['manufacturers', 'admin'] as const,
    adminList: (params: PageParams = {}) => ['manufacturers', 'admin', params] as const,
  },
  products: {
    listBase: ['products', 'list'] as const,
    list: (filters: ProductFilters = {}) => ['products', 'list', filters] as const,
    detail: (productId: string) => ['products', 'detail', productId] as const,
    adminBase: ['products', 'admin'] as const,
    adminList: (params: PageParams = {}) => ['products', 'admin', params] as const,
  },
  reviews: {
    publicBase: (productId: string) => ['reviews', 'public', productId] as const,
    publicList: (productId: string, params: PageParams = {}) =>
      ['reviews', 'public', productId, params] as const,
    adminBase: (productId: string) => ['reviews', 'admin', productId] as const,
    adminList: (productId: string, params: PageParams = {}) =>
      ['reviews', 'admin', productId, params] as const,
  },
  promos: {
    adminBase: (productId: string) => ['promos', 'admin', productId] as const,
    adminList: (filters: AdminPromoFilters) => ['promos', 'admin', filters] as const,
  },
  orders: {
    adminBase: ['orders', 'admin'] as const,
    adminList: (filters: AdminOrderFilters = {}) => ['orders', 'admin', filters] as const,
    detail: (orderId: string) => ['orders', 'detail', orderId] as const,
  },
  admin: {
    me: ['admin', 'me'] as const,
  },
};
EOF

# ============================================================================
# features/catalog/hooks/*
# ============================================================================
cat > "$SRC/features/catalog/hooks/useCategories.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getCategories } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { PageParams } from '../../../types/common';

/**
 * Загружает список активных категорий для фильтра витрины.
 *
 * @param params - Пагинация (limit/offset). По умолчанию бэкенд отдаёт
 *   первые 20 — для выпадающего списка фильтра этого обычно достаточно.
 * @returns Результат React Query с `Paginated<Category>` в `data`.
 */
export function useCategories(params: PageParams = {}) {
  return useQuery({
    queryKey: queryKeys.categories.publicList(params),
    queryFn: () => getCategories(params),
    staleTime: 5 * 60 * 1000, // категории меняются редко — 5 минут кэша достаточно
  });
}
EOF

cat > "$SRC/features/catalog/hooks/useManufacturers.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getManufacturers } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { PageParams } from '../../../types/common';

/**
 * Загружает список активных производителей для фильтра витрины.
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Manufacturer>` в `data`.
 */
export function useManufacturers(params: PageParams = {}) {
  return useQuery({
    queryKey: queryKeys.manufacturers.publicList(params),
    queryFn: () => getManufacturers(params),
    staleTime: 5 * 60 * 1000,
  });
}
EOF

cat > "$SRC/features/catalog/hooks/useProducts.ts" << 'EOF'
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getProducts } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { ProductFilters } from '../../../types/product';

/**
 * Загружает страницу витрины с учётом фильтров.
 *
 * `placeholderData: keepPreviousData` оставляет предыдущую страницу
 * на экране, пока грузится следующая (смена фильтра/страницы) — без
 * этого список на миг мигает пустым/лоадером при каждом клике.
 *
 * @param filters - Фильтры и пагинация каталога.
 * @returns Результат React Query с `Paginated<ProductCatalogItem>` в `data`.
 */
export function useProducts(filters: ProductFilters = {}) {
  return useQuery({
    queryKey: queryKeys.products.list(filters),
    queryFn: () => getProducts(filters),
    placeholderData: keepPreviousData,
  });
}
EOF

# ============================================================================
# features/product-detail/hooks/*
# ============================================================================
cat > "$SRC/features/product-detail/hooks/useProduct.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';

/**
 * Загружает полную карточку товара для страницы товара.
 *
 * @param productId - Идентификатор товара (например, из `useParams`).
 * @returns Результат React Query с `ProductDetail` в `data`.
 */
export function useProduct(productId: string) {
  return useQuery({
    queryKey: queryKeys.products.detail(productId),
    queryFn: () => getProduct(productId),
    enabled: Boolean(productId), // не запускать запрос до появления id
  });
}
EOF

cat > "$SRC/features/product-detail/hooks/useProductReviews.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getProductReviews } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { PageParams } from '../../../types/common';

/**
 * Загружает страницу опубликованных отзывов товара.
 *
 * @param productId - Идентификатор товара.
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Review>` в `data`.
 */
export function useProductReviews(productId: string, params: PageParams = {}) {
  return useQuery({
    queryKey: queryKeys.reviews.publicList(productId, params),
    queryFn: () => getProductReviews(productId, params),
    enabled: Boolean(productId),
  });
}
EOF

cat > "$SRC/features/product-detail/hooks/useCreateReview.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createReview } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { ReviewCreateRequest } from '../../../types/review';

/**
 * Отправляет отзыв на товар (без аутентификации — аккаунтов покупателей нет).
 *
 * Инвалидирует публичный список отзывов, хотя новый отзыв не появится в
 * нём сразу: он уходит на модерацию (`is_approved=false`). Инвалидация —
 * задел на будущее (когда отзыв одобрят), а не ошибка ожидания.
 *
 * @param productId - Идентификатор товара, на который оставляют отзыв.
 * @returns Мутацию React Query, принимающую `ReviewCreateRequest`.
 */
export function useCreateReview(productId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ReviewCreateRequest) => createReview(productId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.publicBase(productId) });
    },
  });
}
EOF

# ============================================================================
# features/cart/*
# ============================================================================
cat > "$SRC/features/cart/types.ts" << 'EOF'
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
EOF

cat > "$SRC/features/cart/cartStore.ts" << 'EOF'
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
EOF

cat > "$SRC/features/cart/hooks/useCart.ts" << 'EOF'
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
EOF

# ============================================================================
# features/checkout/hooks/useCreateOrder.ts
# ============================================================================
cat > "$SRC/features/checkout/hooks/useCreateOrder.ts" << 'EOF'
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
EOF

# ============================================================================
# features/admin-auth/*
# ============================================================================
cat > "$SRC/features/admin-auth/authStore.ts" << 'EOF'
import { create } from 'zustand';

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  clearToken: () => void;
}

/**
 * Хранит JWT администратора только в памяти (НЕ persist, НЕ localStorage).
 *
 * Осознанное упрощение в другую сторону от типичного продакшена: в проде
 * для JWT часто делают httpOnly cookie + refresh-токен, чтобы защититься
 * от кражи токена через XSS. Здесь токен живёт только в памяти вкладки —
 * админ разлогинивается при обновлении страницы, зато не нужно поднимать
 * httpOnly cookie между тремя разными origin'ами ради учебного проекта.
 * Согласуется с TTL access-токена в 30 минут и known_limitations #3.
 */
export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  clearToken: () => set({ token: null }),
}));
EOF

cat > "$SRC/features/admin-auth/hooks/useAdminLogin.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { login } from '../../../api/adminApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../authStore';
import type { LoginRequest } from '../../../types/admin';

/**
 * Логинит администратора и сохраняет access-токен в `authStore`.
 *
 * @returns Мутацию React Query, принимающую `LoginRequest`.
 */
export function useAdminLogin() {
  const setToken = useAuthStore((state) => state.setToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: LoginRequest) => login(body),
    onSuccess: (data) => {
      setToken(data.access_token);
      // Сбрасываем закешированный профиль прошлой сессии (если был) —
      // иначе useCurrentAdmin может на мгновение показать чужие данные.
      queryClient.invalidateQueries({ queryKey: queryKeys.admin.me });
    },
  });
}
EOF

cat > "$SRC/features/admin-auth/hooks/useCurrentAdmin.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getMe } from '../../../api/adminApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../authStore';

/**
 * Загружает профиль текущего администратора через `GET /auth/me`.
 *
 * `enabled` завязан на наличие токена: без него бэкенд всё равно ответит
 * 401, но нет смысла делать заведомо провальный запрос до логина.
 *
 * @returns Результат React Query с `AdminRead` в `data`.
 */
export function useCurrentAdmin() {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.admin.me,
    queryFn: () => getMe(token as string),
    enabled: Boolean(token),
    staleTime: 5 * 60 * 1000,
  });
}
EOF

# ============================================================================
# features/admin-products/hooks/*
# ============================================================================
cat > "$SRC/features/admin-products/hooks/useAdminProducts.ts" << 'EOF'
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getAdminProducts } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PageParams } from '../../../types/common';

/**
 * Загружает страницу товаров для админки (включая is_active === false).
 *
 * ВАЖНО: у `GET /admin/products` нет фильтров по категории/производителю/
 * цене — только пагинация. Фильтрация в UI админки, если понадобится,
 * делается на фронте по уже полученной странице.
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<ProductRead>` в `data`.
 */
export function useAdminProducts(params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.products.adminList(params),
    queryFn: () => getAdminProducts(params, token as string),
    enabled: Boolean(token),
    placeholderData: keepPreviousData,
  });
}
EOF

cat > "$SRC/features/admin-products/hooks/useCreateProduct.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { ProductCreateRequest } from '../../../types/product';

/**
 * Создаёт товар.
 *
 * @returns Мутацию React Query, принимающую `ProductCreateRequest`.
 */
export function useCreateProduct() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ProductCreateRequest) => createProduct(body, token as string),
    onSuccess: () => {
      // Новый товар должен появиться и в админском списке, и (если
      // is_active по умолчанию true) на витрине — инвалидируем оба.
      queryClient.invalidateQueries({ queryKey: queryKeys.products.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
    },
  });
}
EOF

cat > "$SRC/features/admin-products/hooks/useUpdateProduct.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { ProductUpdateRequest } from '../../../types/product';

/**
 * Частично обновляет товар. `quantity` в теле передавать нельзя —
 * см. `ProductUpdateRequest` — остаток этим методом не меняется.
 *
 * @param productId - Идентификатор обновляемого товара.
 * @returns Мутацию React Query, принимающую `ProductUpdateRequest`.
 */
export function useUpdateProduct(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ProductUpdateRequest) => updateProduct(productId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
EOF

cat > "$SRC/features/admin-products/hooks/useDeactivateProduct.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deactivateProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Снимает товар с витрины (физическое удаление запрещено доменной моделью).
 *
 * @returns Мутацию React Query, принимающую `productId`.
 */
export function useDeactivateProduct() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (productId: string) => deactivateProduct(productId, token as string),
    onSuccess: (_data, productId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
EOF

# ============================================================================
# features/admin-catalog-refs/hooks/*
#
# Категории и производители — симметричные CRUD-справочники без
# собственной бизнес-логики (в отличие от товаров). Чтобы не плодить
# по 4 файла на каждый такой справочник, query и все его мутации собраны
# в одном файле на ресурс — весь жизненный цикл виден сразу, без прыжков
# между файлами.
# ============================================================================
cat > "$SRC/features/admin-catalog-refs/hooks/useAdminCategories.ts" << 'EOF'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createCategory,
  deactivateCategory,
  getAdminCategories,
  updateCategory,
} from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { CategoryCreateRequest, CategoryUpdateRequest } from '../../../types/category';
import type { PageParams } from '../../../types/common';

/**
 * Загружает страницу всех категорий для админки (включая скрытые).
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Category>` в `data`.
 */
export function useAdminCategories(params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.categories.adminList(params),
    queryFn: () => getAdminCategories(params, token as string),
    enabled: Boolean(token),
  });
}

/**
 * Создаёт категорию.
 *
 * @returns Мутацию React Query, принимающую `CategoryCreateRequest`.
 */
export function useCreateCategory() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CategoryCreateRequest) => createCategory(body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.adminBase });
    },
  });
}

/**
 * Частично обновляет категорию.
 *
 * @param categoryId - Идентификатор категории.
 * @returns Мутацию React Query, принимающую `CategoryUpdateRequest`.
 */
export function useUpdateCategory(categoryId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CategoryUpdateRequest) => updateCategory(categoryId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.adminBase });
    },
  });
}

/**
 * Скрывает категорию с витрины (физическое удаление запрещено, ON DELETE RESTRICT).
 *
 * @returns Мутацию React Query, принимающую `categoryId`.
 */
export function useDeactivateCategory() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (categoryId: string) => deactivateCategory(categoryId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.adminBase });
    },
  });
}
EOF

cat > "$SRC/features/admin-catalog-refs/hooks/useAdminManufacturers.ts" << 'EOF'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createManufacturer,
  deactivateManufacturer,
  getAdminManufacturers,
  updateManufacturer,
} from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PageParams } from '../../../types/common';
import type {
  ManufacturerCreateRequest,
  ManufacturerUpdateRequest,
} from '../../../types/manufacturer';

/**
 * Загружает страницу всех производителей для админки (включая скрытых).
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Manufacturer>` в `data`.
 */
export function useAdminManufacturers(params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.manufacturers.adminList(params),
    queryFn: () => getAdminManufacturers(params, token as string),
    enabled: Boolean(token),
  });
}

/**
 * Создаёт производителя.
 *
 * @returns Мутацию React Query, принимающую `ManufacturerCreateRequest`.
 */
export function useCreateManufacturer() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ManufacturerCreateRequest) => createManufacturer(body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.manufacturers.adminBase });
    },
  });
}

/**
 * Частично обновляет производителя.
 *
 * @param manufacturerId - Идентификатор производителя.
 * @returns Мутацию React Query, принимающую `ManufacturerUpdateRequest`.
 */
export function useUpdateManufacturer(manufacturerId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ManufacturerUpdateRequest) =>
      updateManufacturer(manufacturerId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.manufacturers.adminBase });
    },
  });
}

/**
 * Скрывает производителя с витрины (физическое удаление запрещено).
 *
 * @returns Мутацию React Query, принимающую `manufacturerId`.
 */
export function useDeactivateManufacturer() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (manufacturerId: string) => deactivateManufacturer(manufacturerId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.manufacturers.adminBase });
    },
  });
}
EOF

# ============================================================================
# features/admin-reviews/hooks/*
# ============================================================================
cat > "$SRC/features/admin-reviews/hooks/usePendingReviews.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getAdminReviewsForProduct } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PageParams } from '../../../types/common';

/**
 * Загружает все отзывы товара для модерации (включая неопубликованные).
 *
 * Имя файла унаследовано от структуры первого шага проектирования, но
 * бэкенд не отдаёт список "все отзывы на модерации сразу по всем
 * товарам" — `product_id` обязателен в `GET /admin/reviews`. Поэтому
 * хук принимает `productId`: экран модерации должен сначала предложить
 * выбрать товар (например, из списка `useAdminProducts`).
 *
 * @param productId - Идентификатор товара.
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Review>` в `data`.
 */
export function usePendingReviews(productId: string, params: PageParams = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.reviews.adminList(productId, params),
    queryFn: () => getAdminReviewsForProduct(productId, params, token as string),
    enabled: Boolean(token) && Boolean(productId),
  });
}
EOF

cat > "$SRC/features/admin-reviews/hooks/useApproveReview.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { moderateReview } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Публикует отзыв (или снимает с публикации — см. `body.is_approved`).
 *
 * `productId` нужен только для точной инвалидации кэша: сам запрос
 * адресуется по `review_id`, но обновить нужно списки именно этого
 * товара — и публичный (отзыв мог опубликоваться), и админский.
 *
 * @param productId - Идентификатор товара, к которому относится отзыв.
 * @returns Мутацию React Query, принимающую `reviewId`.
 */
export function useApproveReview(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewId: string) =>
      moderateReview(reviewId, { is_approved: true }, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.publicBase(productId) });
    },
  });
}
EOF

cat > "$SRC/features/admin-reviews/hooks/useDeleteReview.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteReview } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Физически удаляет отзыв (модерация спама/оскорблений — удаление разрешено доменной моделью).
 *
 * @param productId - Идентификатор товара, к которому относится отзыв (для инвалидации кэша).
 * @returns Мутацию React Query, принимающую `reviewId`.
 */
export function useDeleteReview(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewId: string) => deleteReview(reviewId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.publicBase(productId) });
    },
  });
}
EOF

# ============================================================================
# features/admin-promos/hooks/*
# ============================================================================
cat > "$SRC/features/admin-promos/hooks/useAdminPromos.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getAdminPromos } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { AdminPromoFilters } from '../../../types/promo';

/**
 * Загружает страницу всех акций товара (включая выключенные).
 *
 * `filters.product_id` обязателен — общего списка акций по всем товарам
 * сразу бэкенд не отдаёт. Экран должен сперва предложить выбрать товар.
 *
 * @param filters - Фильтр по товару и пагинация.
 * @returns Результат React Query с `Paginated<Promo>` в `data`.
 */
export function useAdminPromos(filters: AdminPromoFilters) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.promos.adminList(filters),
    queryFn: () => getAdminPromos(filters, token as string),
    enabled: Boolean(token) && Boolean(filters.product_id),
  });
}
EOF

cat > "$SRC/features/admin-promos/hooks/useCreatePromo.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createPromo } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PromoCreateRequest } from '../../../types/promo';

/**
 * Создаёт акцию на товар.
 *
 * Инвалидирует не только список акций товара, но и публичный каталог/
 * карточку товара: `display_price` и `bulk_discount_hint` на витрине
 * зависят от активных акций и должны обновиться сразу после создания.
 *
 * @returns Мутацию React Query, принимающую `PromoCreateRequest`.
 */
export function useCreatePromo() {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: PromoCreateRequest) => createPromo(body, token as string),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promos.adminBase(variables.product_id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(variables.product_id) });
    },
  });
}
EOF

cat > "$SRC/features/admin-promos/hooks/useUpdatePromo.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updatePromo } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { PromoUpdateRequest } from '../../../types/promo';

/**
 * Частично обновляет акцию. `product_id` в теле передавать нельзя —
 * см. `PromoUpdateRequest` — перепривязать акцию к другому товару нельзя.
 *
 * @param productId - Идентификатор товара акции (для инвалидации кэша витрины).
 * @returns Мутацию React Query, принимающую `{ promoId, body }`.
 */
export function useUpdatePromo(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ promoId, body }: { promoId: string; body: PromoUpdateRequest }) =>
      updatePromo(promoId, body, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promos.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
EOF

cat > "$SRC/features/admin-promos/hooks/useDeactivatePromo.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deactivatePromo } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Выключает акцию (физическое удаление запрещено доменной моделью).
 *
 * @param productId - Идентификатор товара акции (для инвалидации кэша витрины).
 * @returns Мутацию React Query, принимающую `promoId`.
 */
export function useDeactivatePromo(productId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (promoId: string) => deactivatePromo(promoId, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promos.adminBase(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.listBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.detail(productId) });
    },
  });
}
EOF

# ============================================================================
# features/admin-orders/hooks/*
# ============================================================================
cat > "$SRC/features/admin-orders/hooks/useAdminOrders.ts" << 'EOF'
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getAdminOrders } from '../../../api/ordersApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { AdminOrderFilters } from '../../../types/order';

/**
 * Загружает страницу заказов с фильтрами по статусу и email покупателя.
 *
 * @param filters - Фильтры и пагинация.
 * @returns Результат React Query с `Paginated<OrderRead>` в `data`.
 */
export function useAdminOrders(filters: AdminOrderFilters = {}) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.orders.adminList(filters),
    queryFn: () => getAdminOrders(filters, token as string),
    enabled: Boolean(token),
    placeholderData: keepPreviousData,
  });
}
EOF

cat > "$SRC/features/admin-orders/hooks/useOrder.ts" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { getOrder } from '../../../api/ordersApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';

/**
 * Загружает детали одного заказа для админки.
 *
 * `GET /orders/{id}` требует прав MANAGE_ORDERS — публичного
 * использования у этого хука нет (решение по order-status: покупатель
 * заказ по ссылке не отслеживает, см. чат).
 *
 * @param orderId - Идентификатор заказа.
 * @returns Результат React Query с `OrderRead` в `data`.
 */
export function useOrder(orderId: string) {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: queryKeys.orders.detail(orderId),
    queryFn: () => getOrder(orderId, token as string),
    enabled: Boolean(token) && Boolean(orderId),
  });
}
EOF

cat > "$SRC/features/admin-orders/hooks/useUpdateOrderStatus.ts" << 'EOF'
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateOrderStatus } from '../../../api/ordersApi';
import { queryKeys } from '../../../lib/queryKeys';
import { useAuthStore } from '../../admin-auth/authStore';
import type { OrderStatus } from '../../../types/enums';

/**
 * Переводит заказ в новый статус. Допустимость перехода (например,
 * `paid` → `shipped`, но не `shipped` → `new`) проверяет бэкенд —
 * хук отправляет статус как есть, без собственной валидации переходов.
 *
 * @param orderId - Идентификатор заказа.
 * @returns Мутацию React Query, принимающую новый `OrderStatus`.
 */
export function useUpdateOrderStatus(orderId: string) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (status: OrderStatus) => updateOrderStatus(orderId, status, token as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.orders.adminBase });
      queryClient.invalidateQueries({ queryKey: queryKeys.orders.detail(orderId) });
    },
  });
}
EOF

echo "Хуки и сторы наполнены для всех фич, кроме admin-management."
echo
echo "Не забудьте установить пакеты (если ещё не установлены):"
echo "  npm install @tanstack/react-query zustand"