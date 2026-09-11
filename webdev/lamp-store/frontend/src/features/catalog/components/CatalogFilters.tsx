import type { ChangeEvent } from 'react';
import { SOCKET_TYPE_LABELS } from '../../../lib/constants';
import type { Category } from '../../../types/category';
import type { SocketType } from '../../../types/enums';
import type { Manufacturer } from '../../../types/manufacturer';
import type { ProductFilters } from '../../../types/product';
import styles from './CatalogFilters.module.css';

interface CatalogFiltersProps {
  filters: ProductFilters;
  onChange: (filters: ProductFilters) => void;
  categories: Category[];
  manufacturers: Manufacturer[];
}

const SOCKET_TYPES = Object.keys(SOCKET_TYPE_LABELS) as SocketType[];

/**
 * Панель фильтров каталога — визуально часть тёмной "панели управления"
 * в шапке страницы (рендерится внутри `<header>` `CatalogPage`, фон
 * наследуется оттуда, здесь заданы только сами элементы управления).
 *
 * Тип цоколя выбирается рядом кнопок-переключателей, а не `<select>` —
 * так виден весь набор сразу, без открытия выпадающего списка; логика
 * та же самая (`update({ socket_type })`), меняется только разметка.
 *
 * Каждое изменение сразу уходит наружу через `onChange`, без отдельной
 * кнопки "Применить". Смена ЛЮБОГО фильтра, кроме листания страниц,
 * сбрасывает `offset` на 0 — иначе легко залипнуть на пустой странице
 * после того, как фильтр сузил выборку сильнее, чем было заказано страниц.
 *
 * @param filters - Текущие значения фильтров (управляемый компонент).
 * @param onChange - Вызывается с новым набором фильтров при любом изменении.
 * @param categories - Список категорий для выпадающего списка.
 * @param manufacturers - Список производителей для выпадающего списка.
 */
export function CatalogFilters({ filters, onChange, categories, manufacturers }: CatalogFiltersProps) {
  function update(patch: Partial<ProductFilters>) {
    onChange({ ...filters, ...patch, offset: 0 });
  }

  function handleSearch(event: ChangeEvent<HTMLInputElement>) {
    update({ search: event.target.value || undefined });
  }

  return (
    <div className={styles.panel}>
      <input
        type="search"
        className={styles.search}
        placeholder="Найти лампу по названию"
        value={filters.search ?? ''}
        onChange={handleSearch}
      />

      <select
        className={styles.select}
        value={filters.category_id ?? ''}
        onChange={(e) => update({ category_id: e.target.value || undefined })}
      >
        <option value="">Все категории</option>
        {categories.map((c) => (
          <option key={c.category_id} value={c.category_id}>
            {c.name}
          </option>
        ))}
      </select>

      <select
        className={styles.select}
        value={filters.manufacturer_id ?? ''}
        onChange={(e) => update({ manufacturer_id: e.target.value || undefined })}
      >
        <option value="">Все производители</option>
        {manufacturers.map((m) => (
          <option key={m.manufacturer_id} value={m.manufacturer_id}>
            {m.name}
          </option>
        ))}
      </select>

      <div className={styles.socketGroup} role="group" aria-label="Тип цоколя">
        <button
          type="button"
          className={!filters.socket_type ? `${styles.socketButton} ${styles.socketButtonActive}` : styles.socketButton}
          onClick={() => update({ socket_type: undefined })}
        >
          Любой цоколь
        </button>
        {SOCKET_TYPES.map((s) => (
          <button
            key={s}
            type="button"
            title={SOCKET_TYPE_LABELS[s]}
            className={filters.socket_type === s ? `${styles.socketButton} ${styles.socketButtonActive}` : styles.socketButton}
            onClick={() => update({ socket_type: s })}
          >
            {s}
          </button>
        ))}
      </div>

      <div className={styles.priceRange}>
        <input
          type="number"
          min={0}
          inputMode="decimal"
          className={styles.priceInput}
          placeholder="Цена от"
          value={filters.min_price ?? ''}
          onChange={(e) => update({ min_price: e.target.value || undefined })}
        />
        <span className={styles.priceDash}>—</span>
        <input
          type="number"
          min={0}
          inputMode="decimal"
          className={styles.priceInput}
          placeholder="до"
          value={filters.max_price ?? ''}
          onChange={(e) => update({ max_price: e.target.value || undefined })}
        />
      </div>

      <label className={styles.checkbox}>
        <input
          type="checkbox"
          checked={filters.in_stock_only ?? false}
          onChange={(e) => update({ in_stock_only: e.target.checked || undefined })}
        />
        Только в наличии
      </label>
    </div>
  );
}
