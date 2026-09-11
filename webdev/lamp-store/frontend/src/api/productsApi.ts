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
