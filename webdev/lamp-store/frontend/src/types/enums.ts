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
