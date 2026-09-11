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
