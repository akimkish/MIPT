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
