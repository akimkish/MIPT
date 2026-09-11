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
