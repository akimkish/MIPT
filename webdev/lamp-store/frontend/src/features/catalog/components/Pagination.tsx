import styles from './Pagination.module.css';

interface PaginationProps {
  limit: number;
  offset: number;
  total: number;
  onChange: (offset: number) => void;
}

/**
 * Постраничная навигация по `limit`/`offset` — форме пагинации, которую
 * реально отдаёт бэкенд (`PaginatedResponse`), а не по номеру страницы
 * с отдельным полем `page`.
 *
 * @param limit - Размер страницы.
 * @param offset - Текущее смещение.
 * @param total - Общее количество элементов (из ответа сервера).
 * @param onChange - Вызывается с новым `offset` при переходе на другую страницу.
 */
export function Pagination({ limit, offset, total, onChange }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  if (totalPages <= 1) return null;

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        className={styles.button}
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        Назад
      </button>
      <span className={styles.status}>
        Страница {currentPage} из {totalPages}
      </span>
      <button
        type="button"
        className={styles.button}
        disabled={currentPage >= totalPages}
        onClick={() => onChange(offset + limit)}
      >
        Вперёд
      </button>
    </div>
  );
}
