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
