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
