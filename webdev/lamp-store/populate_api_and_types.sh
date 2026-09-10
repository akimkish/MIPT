#!/usr/bin/env bash
#
# ВЕРСИЯ 2 — заменяет предыдущий populate_api_and_types.sh.
# Причина: первая версия типов/клиентов была написана по одним лишь именам
# файлов бэкенда (до того, как были присланы реальные роуты и Pydantic-схемы)
# и не совпадала с реальным контрактом в нескольких местах — см. пояснение
# в чате. Эта версия построена по факту присланного кода.
#
# Наполняет содержимым файлы frontend/src/types/ и frontend/src/api/.
# Запускать ПОСЛЕ create_frontend_structure.sh — ИЗ КОРНЯ РЕПОЗИТОРИЯ:
#
#   ./populate_api_and_types.sh
#
# Идемпотентен: каждый `cat > file` полностью перезаписывает файл.

set -euo pipefail

if [[ ! -d "frontend/src" ]]; then
  echo "Ошибка: 'frontend/src' не найдена." >&2
  echo "Сначала запустите create_frontend_structure.sh, затем этот скрипт" >&2
  echo "из корня репозитория lamp-store/." >&2
  exit 1
fi

SRC="frontend/src"

# ============================================================================
# types/common.ts
# ============================================================================
cat > "$SRC/types/common.ts" << 'EOF'
/**
 * UUID4 в текстовом виде, как его отдаёт Pydantic
 * (например, "3fa85f64-5717-4562-b3fc-2c963f66afa6").
 */
export type UUID = string;

/** ISO 8601 дата-время с таймзоной, как её сериализует Pydantic (datetime). */
export type ISODateTime = string;

/**
 * Decimal-поле с бэкенда, сериализованное в JSON как строка (не number),
 * чтобы не терять точность. Арифметика над ним на фронте не выполняется —
 * только форматирование для отображения (см. lib/money.ts).
 */
export type DecimalString = string;

/**
 * Ответ пагинированного списка.
 *
 * Точно соответствует `schemas/common.py::PaginatedResponse`:
 * только `items` и `total`, без `page`/`page_size` — те вычисляются
 * на фронте из `limit`/`offset`, если понадобятся для UI пагинатора.
 */
export interface Paginated<T> {
  items: T[];
  total: number;
}

/**
 * Параметры пагинации запроса.
 *
 * Точно соответствует `schemas/common.py::PaginationParams`:
 * `limit` по умолчанию 20 (1..100), `offset` по умолчанию 0.
 */
export interface PageParams {
  limit?: number;
  offset?: number;
}
EOF

# ============================================================================
# types/enums.ts
# ============================================================================
cat > "$SRC/types/enums.ts" << 'EOF'
/** Тип цоколя лампы. Совпадает со значениями `app.models.enums.SocketType`. */
export type SocketType = 'E14' | 'E27' | 'E40' | 'G4' | 'G9' | 'G13' | 'GU10' | 'GU5.3';

/** Тип скидки промо-акции. `app.models.enums.DiscountType`. */
export type DiscountType = 'percent' | 'fixed';

/** Статус заказа. `app.models.enums.OrderStatus`. */
export type OrderStatus =
  | 'pending'
  | 'failed'
  | 'new'
  | 'paid'
  | 'shipped'
  | 'completed'
  | 'cancelled';

/** Роль администратора. Источник истины — ROLE_PERMISSIONS на бэкенде. */
export type RoleName = 'superadmin' | 'manager' | 'moderator';
EOF

# ============================================================================
# types/category.ts
# ============================================================================
cat > "$SRC/types/category.ts" << 'EOF'
import type { ISODateTime, UUID } from './common';

/**
 * Категория товаров каталога.
 *
 * ДОПУЩЕНИЕ: `schemas/category.py` не был прислан, поле-состав взят по
 * аналогии с ORM-моделью `categories` из project_context (category_id,
 * name, description, is_active, created_at, updated_at) и по тому, как
 * `CategoryRead` используется в `api/v1/categories.py`. Сверить при
 * первом реальном вызове.
 */
export interface Category {
  category_id: UUID;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

/** Тело POST /admin/categories — по аналогии с ProductCreate/PromoCreate. */
export interface CategoryCreateRequest {
  name: string;
  description?: string;
}

/** Тело PATCH /admin/categories/{id}. */
export type CategoryUpdateRequest = Partial<CategoryCreateRequest> & {
  is_active?: boolean;
};
EOF

# ============================================================================
# types/manufacturer.ts
# ============================================================================
cat > "$SRC/types/manufacturer.ts" << 'EOF'
import type { ISODateTime, UUID } from './common';

/**
 * Производитель товаров каталога.
 *
 * ДОПУЩЕНИЕ: `schemas/manufacturer.py` не был прислан — состав полей по
 * аналогии с ORM-моделью `manufacturers`. Сверить при первом реальном вызове.
 */
export interface Manufacturer {
  manufacturer_id: UUID;
  name: string;
  description: string | null;
  logo_url: string | null;
  is_active: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface ManufacturerCreateRequest {
  name: string;
  description?: string;
  logo_url?: string;
}

export type ManufacturerUpdateRequest = Partial<ManufacturerCreateRequest> & {
  is_active?: boolean;
};
EOF

# ============================================================================
# types/product.ts
# ============================================================================
cat > "$SRC/types/product.ts" << 'EOF'
import type { Category } from './category';
import type { DecimalString, ISODateTime, UUID } from './common';
import type { SocketType } from './enums';
import type { Manufacturer } from './manufacturer';

/**
 * Товар в административном представлении: `GET/POST/PATCH/DELETE
 * /admin/products` (schemas/product.py::ProductRead).
 *
 * В отличие от витрины НЕ содержит `display_price`/`bulk_discount_hint`
 * (админке они не нужны — цену считает сервис только для покупателя) и
 * НЕ содержит вложенных `category`/`manufacturer` — только их id.
 * Если для таблицы в админке нужны названия категории/производителя,
 * сопоставлять по `category_id`/`manufacturer_id` с данными
 * `useAdminCategories`/`useAdminManufacturers` на фронте, а не ждать
 * их от этого эндпоинта.
 */
export interface ProductRead {
  product_id: UUID;
  product_name: string;
  sku: string;
  category_id: UUID;
  manufacturer_id: UUID;
  price: DecimalString;
  quantity: number;
  description: string | null;
  power_watts: DecimalString;
  socket_type: SocketType;
  color_temperature_k: number;
  image_url: string | null;
  is_active: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

/** Элемент публичной витрины: `GET /products` (ProductCatalogItem). */
export interface ProductCatalogItem extends ProductRead {
  /** Цена при qty=1 с учётом лучшей подходящей акции. */
  display_price: DecimalString;
  /** Например "от 5 шт. дешевле", если есть акция с min_quantity > 1. */
  bulk_discount_hint: string | null;
}

/** Полная карточка товара: `GET /products/{id}` (ProductDetail). */
export interface ProductDetail extends ProductCatalogItem {
  category: Category;
  manufacturer: Manufacturer;
  average_rating: number | null;
}

/**
 * Тело POST /admin/products (ProductCreate).
 *
 * `quantity` здесь ЕСТЬ (начальный остаток при создании товара) —
 * в отличие от Update ниже.
 */
export interface ProductCreateRequest {
  product_name: string;
  sku: string;
  category_id: UUID;
  manufacturer_id: UUID;
  price: DecimalString;
  quantity: number;
  description?: string;
  power_watts: DecimalString;
  socket_type: SocketType;
  color_temperature_k: number;
  image_url?: string;
}

/**
 * Тело PATCH /admin/products/{id} (ProductUpdate).
 *
 * ВАЖНО: `quantity` здесь НЕТ вообще, не только необязателен — бэкенд
 * не даёт менять остаток этим методом (см. докстринг `update_product`
 * в products.py: "остаток этим методом не меняется"). Списание/пополнение
 * остатка — отдельный внутренний механизм (stock_operations), фронту
 * админки товаров сюда лезть не нужно.
 */
export type ProductUpdateRequest = Partial<Omit<ProductCreateRequest, 'quantity'>> & {
  is_active?: boolean;
};

/** Параметры фильтрации публичного каталога — `GET /products`. */
export interface ProductFilters {
  category_id?: UUID;
  manufacturer_id?: UUID;
  socket_type?: SocketType;
  min_price?: DecimalString;
  max_price?: DecimalString;
  search?: string;
  in_stock_only?: boolean;
  limit?: number;
  offset?: number;
}
EOF

# ============================================================================
# types/review.ts
# ============================================================================
cat > "$SRC/types/review.ts" << 'EOF'
import type { ISODateTime, UUID } from './common';

/** Отзыв на товар. На витрине показываются только is_approved === true. */
export interface Review {
  review_id: UUID;
  product_id: UUID;
  user_name: string;
  user_email: string;
  description: string | null;
  /** Целое число от 1 до 5. */
  rating: number;
  is_approved: boolean;
  created_at: ISODateTime;
}

/**
 * Тело POST /products/{product_id}/reviews (ReviewCreate).
 *
 * `product_id` ОБЯЗАН присутствовать в теле и совпадать с `product_id`
 * из пути — бэкенд явно сверяет их и отдаёт 400 при несовпадении
 * (см. `create_review` в reviews.py). Это легко забыть при сборке формы.
 */
export interface ReviewCreateRequest {
  product_id: UUID;
  user_name: string;
  user_email: string;
  description?: string;
  rating: number;
}

/** Тело PATCH /admin/reviews/{id} — публикация/снятие с публикации. */
export interface ReviewModerateRequest {
  is_approved: boolean;
}
EOF

# ============================================================================
# types/promo.ts
# ============================================================================
cat > "$SRC/types/promo.ts" << 'EOF'
import type { DecimalString, ISODateTime, UUID } from './common';
import type { DiscountType } from './enums';

/** Промо-акция на товар. */
export interface Promo {
  promo_id: UUID;
  promo_name: string;
  description: string | null;
  discount_type: DiscountType;
  discount: DecimalString;
  product_id: UUID;
  min_quantity: number;
  valid_from: ISODateTime;
  valid_to: ISODateTime;
  is_active: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

/** Тело POST /admin/promos (PromoCreate). `min_quantity` необязателен — default 1. */
export interface PromoCreateRequest {
  promo_name: string;
  description?: string;
  discount_type: DiscountType;
  discount: DecimalString;
  product_id: UUID;
  min_quantity?: number;
  valid_from: ISODateTime;
  valid_to: ISODateTime;
}

/**
 * Тело PATCH /admin/promos/{id} (PromoUpdate).
 *
 * ВАЖНО: `product_id` здесь НЕТ вообще — привязку акции к другому товару
 * сменить нельзя, только пересоздать акцию.
 */
export type PromoUpdateRequest = Partial<Omit<PromoCreateRequest, 'product_id'>> & {
  is_active?: boolean;
};

/**
 * Фильтр GET /admin/promos.
 *
 * `product_id` ОБЯЗАТЕЛЕН на бэкенде (`Query(...)` без default) — общего
 * списка всех акций сразу по всем товарам эндпоинт не отдаёт. Экран
 * "Промо" в админке должен сперва предложить выбрать товар.
 */
export interface AdminPromoFilters {
  product_id: UUID;
  limit?: number;
  offset?: number;
}
EOF

# ============================================================================
# types/order.ts
# ============================================================================
cat > "$SRC/types/order.ts" << 'EOF'
import type { DecimalString, ISODateTime, UUID } from './common';
import type { OrderStatus } from './enums';

/**
 * Позиция заказа в ответах API — неизменяемый снимок товара.
 *
 * ДОПУЩЕНИЕ: `schemas/order_item.py` не был прислан, состав полей взят
 * из ORM-модели `order_items` в project_context (совпадает с исходным
 * примером ответа API из первого промпта). Сверить при первом вызове.
 */
export interface OrderItem {
  item_id: UUID;
  external_product_id: UUID;
  product_name: string;
  sku: string;
  image_url: string | null;
  item_quantity: number;
  original_unit_price: DecimalString;
  unit_price: DecimalString;
  promo_id: UUID | null;
  total_price: DecimalString;
  created_at: ISODateTime;
}

/** Заказ, как его отдаёт POST /orders, GET /orders и GET /orders/{id} (OrderRead). */
export interface OrderRead {
  order_id: UUID;
  idempotency_key: string;
  user_name: string;
  phone: string;
  email: string;
  delivery_address: string;
  total_price: DecimalString;
  status: OrderStatus;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  items: OrderItem[];
}

/** Одна позиция в теле запроса на создание заказа (OrderItemCreate). */
export interface OrderItemRequest {
  external_product_id: UUID;
  item_quantity: number;
}

/**
 * Тело POST /orders (OrderCreate). Публичный эндпоинт, без токена.
 *
 * Намеренно не содержит цен, order_id, статуса — их считает и подставляет
 * бэкенд (products_service отвечает за цены/скидки на своей стороне вызова,
 * orders_service — за сумму и статус).
 */
export interface OrderCreateRequest {
  /** Генерируется на клиенте (uuid v4) — защищает от дублей при повторной отправке. */
  idempotency_key: string;
  user_name: string;
  phone: string;
  email: string;
  delivery_address: string;
  items: OrderItemRequest[];
}

/** Тело PATCH /admin/orders/{id}/status (OrderStatusUpdate). */
export interface OrderStatusUpdateRequest {
  status: OrderStatus;
}

/** Фильтры GET /admin/orders. */
export interface AdminOrderFilters {
  status?: OrderStatus;
  email?: string;
  limit?: number;
  offset?: number;
}
EOF

# ============================================================================
# types/admin.ts
# ============================================================================
cat > "$SRC/types/admin.ts" << 'EOF'
import type { ISODateTime, UUID } from './common';
import type { RoleName } from './enums';

/**
 * Администратор без password_hash (AdminRead / MeResponse).
 *
 * ДОПУЩЕНИЕ: `schemas/admin.py` не был прислан — состав полей взят по
 * аналогии с ORM-моделью `admins` из project_context, за вычетом
 * `password_hash` (он не покидает admin_service по domain_decisions).
 * Сверить при первом вызове GET /auth/me.
 */
export interface AdminRead {
  admin_id: UUID;
  email: string;
  full_name: string;
  role_name: RoleName;
  is_active: boolean;
  failed_login_attempts: number;
  locked_until: ISODateTime | null;
  last_login: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface LoginRequest {
  email: string;
  password: string;
}

/** Ответ POST /auth/login (TokenResponse). Refresh-токена нет — только повторный вход. */
export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}

/**
 * ДОПУЩЕНИЕ: эндпоинты управления другими админами (`admins.py`) не были
 * прислан. Типы ниже — черновик по аналогии с остальными admin-CRUD
 * ресурсами (products/categories), сверить при получении реального файла.
 */
export interface AdminCreateRequest {
  email: string;
  password: string;
  full_name: string;
  role_name: RoleName;
}

export interface RoleChangeRequest {
  new_role: RoleName;
}
EOF

# ============================================================================
# api/errors.ts
# ============================================================================
cat > "$SRC/api/errors.ts" << 'EOF'
/** Форма тела ошибки, которую отдаёт FastAPI (422 — список, остальное — строка/объект). */
export interface ApiErrorBody {
  detail?: string | { msg: string; type: string }[] | { code: string; message: string; details: unknown };
}

/**
 * Единая ошибка HTTP-запроса к любому из трёх бэкенд-сервисов.
 *
 * Учитывает две разные формы `detail`, реально встречающиеся в бэкенде:
 * стандартную FastAPI-валидацию (список `{msg, type}`) и доменные ошибки
 * orders_service вида `{code, message, details}` (см. `create_order`
 * в orders.py: 409 при дубле/нехватке остатка, 503 при недоступности
 * products_service).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | undefined;

  constructor(status: number, body: ApiErrorBody | undefined, message?: string) {
    super(message ?? ApiError.extractMessage(body) ?? `Запрос завершился со статусом ${status}`);
    this.status = status;
    this.body = body;
    this.name = 'ApiError';
  }

  /**
   * Достаёт человекочитаемое сообщение из тела ошибки в любой из известных форм.
   *
   * @param body - Тело ответа, распарсенное как JSON, либо undefined.
   * @returns Сообщение об ошибке либо undefined.
   */
  private static extractMessage(body: ApiErrorBody | undefined): string | undefined {
    if (!body?.detail) return undefined;
    if (typeof body.detail === 'string') return body.detail;
    if ('message' in body.detail) return body.detail.message;
    return body.detail.map((e) => e.msg).join('; ');
  }
}
EOF

# ============================================================================
# api/httpClient.ts (без изменений по сути — переносим как есть)
# ============================================================================
cat > "$SRC/api/httpClient.ts" << 'EOF'
import { ApiError, type ApiErrorBody } from './errors';

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE';

/** Допустимые значения query-параметра — то, что осмысленно кладётся в URL. */
type QueryValue = string | number | boolean | undefined;

interface RequestOptions {
  method?: HttpMethod;
  body?: unknown;
  /** JWT для защищённых (админских) эндпоинтов. Публичные запросы его не передают. */
  token?: string;
  /**
   * Типизирован как `object`, а не `Record<string, QueryValue>` намеренно:
   * конкретные типы фильтров (`ProductFilters`, `PageParams` и т.п.)
   * объявлены как обычные интерфейсы без index signature, и TypeScript
   * в strict-режиме не разрешает передавать такой интерфейс туда, где
   * ожидается `Record<string, ...>` — это реальная ошибка компиляции,
   * а не стилистическая придирка (проверено `tsc --noEmit`). `object`
   * принимает любой из этих интерфейсов, а `buildQueryString` внутри
   * безопасно сужает тип через `as` до `Record<string, QueryValue>`.
   */
  searchParams?: object;
}

/**
 * Строит query-строку из объекта параметров, отбрасывая undefined/null —
 * иначе fetch отправит буквально "?category_id=undefined" на сервер.
 *
 * @param params - Параметры фильтра/пагинации (любой плоский объект).
 * @returns Строка вида "?a=1&b=2" либо "" если параметров нет.
 */
function buildQueryString(params?: object): string {
  if (!params) return '';
  const entries = Object.entries(params as Record<string, QueryValue>).filter(
    ([, v]) => v !== undefined && v !== null,
  );
  if (entries.length === 0) return '';
  const search = new URLSearchParams();
  for (const [key, value] of entries) {
    search.set(key, String(value));
  }
  return `?${search.toString()}`;
}

/**
 * Создаёт HTTP-клиент для одного бэкенд-сервиса.
 *
 * Каждый из трёх сервисов (products/orders/admin) живёт на своём origin —
 * единого API-gateway в проекте нет. Клиент строится вокруг конкретного
 * baseUrl, а не является общим singleton'ом.
 *
 * @param baseUrl - Базовый URL сервиса, например `import.meta.env.VITE_PRODUCTS_API_URL`.
 * @returns Объект с методами get/post/patch/delete, типизированными дженериком.
 */
export function createHttpClient(baseUrl: string) {
  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, token, searchParams } = options;

    const headers: Record<string, string> = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${baseUrl}${path}${buildQueryString(searchParams)}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      let errorBody: ApiErrorBody | undefined;
      try {
        errorBody = (await response.json()) as ApiErrorBody;
      } catch {
        // Тело не JSON — ApiError подставит дефолтное сообщение по статус-коду.
      }
      throw new ApiError(response.status, errorBody);
    }

    // 204 No Content (например, delete_review) — тела ответа нет вообще.
    if (response.status === 204) return undefined as T;

    return (await response.json()) as T;
  }

  return {
    get: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
      request<T>(path, { ...options, method: 'GET' }),
    post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
      request<T>(path, { ...options, method: 'POST', body }),
    patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
      request<T>(path, { ...options, method: 'PATCH', body }),
    delete: <T = void>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
      request<T>(path, { ...options, method: 'DELETE' }),
  };
}

export type HttpClient = ReturnType<typeof createHttpClient>;
EOF

# ============================================================================
# api/productsApi.ts
# ============================================================================
cat > "$SRC/api/productsApi.ts" << 'EOF'
import type { Category, CategoryCreateRequest, CategoryUpdateRequest } from '../types/category';
import type { PageParams, Paginated } from '../types/common';
import type {
  Manufacturer,
  ManufacturerCreateRequest,
  ManufacturerUpdateRequest,
} from '../types/manufacturer';
import type {
  ProductCatalogItem,
  ProductCreateRequest,
  ProductDetail,
  ProductFilters,
  ProductRead,
  ProductUpdateRequest,
} from '../types/product';
import type { AdminPromoFilters, Promo, PromoCreateRequest, PromoUpdateRequest } from '../types/promo';
import type { Review, ReviewCreateRequest, ReviewModerateRequest } from '../types/review';
import { createHttpClient } from './httpClient';

const client = createHttpClient(import.meta.env.VITE_PRODUCTS_API_URL);

// --- Витрина: публичные эндпоинты, без токена --------------------------------

export function getCategories(params: PageParams = {}): Promise<Paginated<Category>> {
  return client.get<Paginated<Category>>('/api/v1/categories', { searchParams: params });
}

export function getManufacturers(params: PageParams = {}): Promise<Paginated<Manufacturer>> {
  return client.get<Paginated<Manufacturer>>('/api/v1/manufacturers', { searchParams: params });
}

export function getProducts(filters: ProductFilters = {}): Promise<Paginated<ProductCatalogItem>> {
  return client.get<Paginated<ProductCatalogItem>>('/api/v1/products', { searchParams: filters });
}

export function getProduct(productId: string): Promise<ProductDetail> {
  return client.get<ProductDetail>(`/api/v1/products/${productId}`);
}

/** Публичный список отдаёт только is_approved === true — фильтрация на бэкенде. */
export function getProductReviews(
  productId: string,
  params: PageParams = {},
): Promise<Paginated<Review>> {
  return client.get<Paginated<Review>>(`/api/v1/products/${productId}/reviews`, {
    searchParams: params,
  });
}

/** `body.product_id` обязан совпадать с `productId` из пути — иначе бэкенд отдаст 400. */
export function createReview(productId: string, body: ReviewCreateRequest): Promise<Review> {
  return client.post<Review>(`/api/v1/products/${productId}/reviews`, body);
}

// --- Админка: товары (требуют JWT) -------------------------------------------

/**
 * У `GET /admin/products` НЕТ фильтров по категории/производителю/цене —
 * только пагинация. Если понадобится фильтрация в админке, фильтровать
 * придётся на фронте либо просить бэкенд расширить эндпоинт.
 */
export function getAdminProducts(
  params: PageParams,
  token: string,
): Promise<Paginated<ProductRead>> {
  return client.get<Paginated<ProductRead>>('/api/v1/admin/products', {
    searchParams: params,
    token,
  });
}

export function createProduct(body: ProductCreateRequest, token: string): Promise<ProductRead> {
  return client.post<ProductRead>('/api/v1/admin/products', body, { token });
}

/** `quantity` в `body` не передавать — эндпоинт его не принимает (см. ProductUpdateRequest). */
export function updateProduct(
  productId: string,
  body: ProductUpdateRequest,
  token: string,
): Promise<ProductRead> {
  return client.patch<ProductRead>(`/api/v1/admin/products/${productId}`, body, { token });
}

/**
 * Снимает товар с витрины (физическое удаление запрещено).
 *
 * ВАЖНО: несмотря на HTTP DELETE, эндпоинт возвращает 200 с деактивированным
 * товаром, а не 204 — не игнорировать тело ответа.
 */
export function deactivateProduct(productId: string, token: string): Promise<ProductRead> {
  return client.delete<ProductRead>(`/api/v1/admin/products/${productId}`, { token });
}

// --- Админка: категории -------------------------------------------------------

export function getAdminCategories(
  params: PageParams,
  token: string,
): Promise<Paginated<Category>> {
  return client.get<Paginated<Category>>('/api/v1/admin/categories', {
    searchParams: params,
    token,
  });
}

export function createCategory(body: CategoryCreateRequest, token: string): Promise<Category> {
  return client.post<Category>('/api/v1/admin/categories', body, { token });
}

export function updateCategory(
  categoryId: string,
  body: CategoryUpdateRequest,
  token: string,
): Promise<Category> {
  return client.patch<Category>(`/api/v1/admin/categories/${categoryId}`, body, { token });
}

/** Тоже 200 с телом, не 204 — по аналогии с товарами и промо. */
export function deactivateCategory(categoryId: string, token: string): Promise<Category> {
  return client.delete<Category>(`/api/v1/admin/categories/${categoryId}`, { token });
}

// --- Админка: производители ----------------------------------------------------

export function getAdminManufacturers(
  params: PageParams,
  token: string,
): Promise<Paginated<Manufacturer>> {
  return client.get<Paginated<Manufacturer>>('/api/v1/admin/manufacturers', {
    searchParams: params,
    token,
  });
}

export function createManufacturer(
  body: ManufacturerCreateRequest,
  token: string,
): Promise<Manufacturer> {
  return client.post<Manufacturer>('/api/v1/admin/manufacturers', body, { token });
}

export function updateManufacturer(
  manufacturerId: string,
  body: ManufacturerUpdateRequest,
  token: string,
): Promise<Manufacturer> {
  return client.patch<Manufacturer>(`/api/v1/admin/manufacturers/${manufacturerId}`, body, {
    token,
  });
}

export function deactivateManufacturer(
  manufacturerId: string,
  token: string,
): Promise<Manufacturer> {
  return client.delete<Manufacturer>(`/api/v1/admin/manufacturers/${manufacturerId}`, { token });
}

// --- Админка: модерация отзывов -------------------------------------------------

/**
 * `productId` уходит query-параметром `product_id` — общего списка "все
 * отзывы на модерации по всем товарам" эндпоинт не даёт, только по одному
 * товару за раз (см. `admin_list_reviews_for_product` в reviews.py).
 */
export function getAdminReviewsForProduct(
  productId: string,
  params: PageParams,
  token: string,
): Promise<Paginated<Review>> {
  return client.get<Paginated<Review>>('/api/v1/admin/reviews', {
    searchParams: { product_id: productId, ...params },
    token,
  });
}

export function moderateReview(
  reviewId: string,
  body: ReviewModerateRequest,
  token: string,
): Promise<Review> {
  return client.patch<Review>(`/api/v1/admin/reviews/${reviewId}`, body, { token });
}

/** Физическое удаление разрешено доменной моделью (модерация спама) — реально 204. */
export function deleteReview(reviewId: string, token: string): Promise<void> {
  return client.delete<void>(`/api/v1/admin/reviews/${reviewId}`, { token });
}

// --- Админка: промо-акции ----------------------------------------------------------

/** `filters.product_id` обязателен — см. AdminPromoFilters. */
export function getAdminPromos(
  filters: AdminPromoFilters,
  token: string,
): Promise<Paginated<Promo>> {
  return client.get<Paginated<Promo>>('/api/v1/admin/promos', { searchParams: filters, token });
}

export function createPromo(body: PromoCreateRequest, token: string): Promise<Promo> {
  return client.post<Promo>('/api/v1/admin/promos', body, { token });
}

/** `product_id` в `body` не передавать — эндпоинт его не принимает (см. PromoUpdateRequest). */
export function updatePromo(
  promoId: string,
  body: PromoUpdateRequest,
  token: string,
): Promise<Promo> {
  return client.patch<Promo>(`/api/v1/admin/promos/${promoId}`, body, { token });
}

/** Выключает акцию (физическое удаление запрещено). 200 с телом, не 204. */
export function deactivatePromo(promoId: string, token: string): Promise<Promo> {
  return client.delete<Promo>(`/api/v1/admin/promos/${promoId}`, { token });
}
EOF

# ============================================================================
# api/ordersApi.ts
# ============================================================================
cat > "$SRC/api/ordersApi.ts" << 'EOF'
import type { AdminOrderFilters, OrderCreateRequest, OrderRead } from '../types/order';
import type { Paginated } from '../types/common';
import type { OrderStatus } from '../types/enums';
import { createHttpClient } from './httpClient';

const client = createHttpClient(import.meta.env.VITE_ORDERS_API_URL);

/**
 * Оформляет заказ. Единственный публичный эндпоинт этого сервиса —
 * учётных записей у покупателей нет, аутентификация не требуется.
 *
 * При 409 (дубль/нехватка остатка/товар снят с продажи) и 503
 * (products_service недоступен) бэкенд кладёт структурированную ошибку
 * `{code, message, details}` в `detail` — см. ApiError в errors.ts.
 */
export function createOrder(body: OrderCreateRequest): Promise<OrderRead> {
  return client.post<OrderRead>('/api/v1/orders', body);
}

// --- Админка: заказы (требуют JWT) --------------------------------------------

/**
 * ВАЖНО: `GET /orders/{id}` тоже требует прав MANAGE_ORDERS — публичного
 * эндпоинта "посмотреть свой заказ по ссылке" в бэкенде НЕТ. Единственный
 * источник данных о заказе для покупателя — ответ на `createOrder` в
 * момент оформления. Экран отдельного отслеживания заказа по id для
 * незалогиненного покупателя на данный момент не реализуем без изменений
 * на бэкенде — уточнить, нужен ли отдельный публичный эндпоинт.
 */
export function getOrder(orderId: string, token: string): Promise<OrderRead> {
  return client.get<OrderRead>(`/api/v1/orders/${orderId}`, { token });
}

export function getAdminOrders(
  filters: AdminOrderFilters,
  token: string,
): Promise<Paginated<OrderRead>> {
  return client.get<Paginated<OrderRead>>('/api/v1/orders', { searchParams: filters, token });
}

/** Оплаты нет — статус paid/shipped/completed проставляет админ вручную. */
export function updateOrderStatus(
  orderId: string,
  status: OrderStatus,
  token: string,
): Promise<OrderRead> {
  return client.patch<OrderRead>(`/api/v1/orders/${orderId}/status`, { status }, { token });
}
EOF

# ============================================================================
# api/adminApi.ts
# ============================================================================
cat > "$SRC/api/adminApi.ts" << 'EOF'
import type {
  AdminCreateRequest,
  AdminRead,
  LoginRequest,
  RoleChangeRequest,
  TokenResponse,
} from '../types/admin';
import { createHttpClient } from './httpClient';

const client = createHttpClient(import.meta.env.VITE_ADMIN_API_URL);

export function login(body: LoginRequest): Promise<TokenResponse> {
  return client.post<TokenResponse>('/api/v1/auth/login', body);
}

/**
 * Профиль администратора, выписавшего переданный токен.
 *
 * Закрывает открытый вопрос предыдущего шага: claims в самом JWT
 * decode-ить на клиенте не нужно — есть выделенный эндпоинт `/auth/me`.
 */
export function getMe(token: string): Promise<AdminRead> {
  return client.get<AdminRead>('/api/v1/auth/me', { token });
}

/**
 * ДОПУЩЕНИЕ: файл `admins.py` (управление другими админами) не был
 * прислан. Функции ниже — черновик по аналогии с остальными admin-CRUD
 * ресурсами (products/categories/manufacturers). Пути и формы точно
 * сверить, когда файл будет доступен.
 */

export function getAdmins(token: string): Promise<AdminRead[]> {
  return client.get<AdminRead[]>('/api/v1/admins', { token });
}

export function createAdmin(body: AdminCreateRequest, token: string): Promise<AdminRead> {
  return client.post<AdminRead>('/api/v1/admins', body, { token });
}

/** Деактивированный админ сохраняет доступ до истечения TTL уже выданного токена
 * (осознанное упрощение, known_limitations #3) — это не баг фронта. */
export function deactivateAdmin(adminId: string, token: string): Promise<void> {
  return client.delete<void>(`/api/v1/admins/${adminId}`, { token });
}

export function changeAdminRole(
  adminId: string,
  body: RoleChangeRequest,
  token: string,
): Promise<AdminRead> {
  return client.patch<AdminRead>(`/api/v1/admins/${adminId}/role`, body, { token });
}
EOF

echo "Файлы api/ и types/ обновлены по реальным схемам бэкенда."
echo
echo "ОТКРЫТЫЕ ВОПРОСЫ (не блокируют текущий код, но требуют решения):"
echo "1. Нет публичного GET /orders/{id} для покупателя без токена — экран"
echo "   отслеживания заказа по ссылке нереализуем как задумано. Нужно решить:"
echo "   убрать фичу order-status или просить отдельный публичный эндпоинт."
echo "2. admins.py (управление админами) не был прислан — adminApi.ts в этой"
echo "   части черновой, сверить при получении файла."
echo "3. schemas/category.py, manufacturer.py, admin.py — поля Category/"
echo "   Manufacturer/AdminRead взяты по аналогии с ORM-моделями, не из схем."
echo
echo "ВАЖНО: для TypeScript-типизации import.meta.env добавьте (если ещё нет)"
echo "в frontend/src/vite-env.d.ts: /// <reference types=\"vite/client\" />"