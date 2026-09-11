import type { OrderStatus, RoleName, SocketType } from '../types/enums';

/** Человекочитаемые подписи типов цоколя — для селектов фильтра и карточки товара. */
export const SOCKET_TYPE_LABELS: Record<SocketType, string> = {
  E14: 'E14 (миньон)',
  E27: 'E27 (стандартный)',
  E40: 'E40 (промышленный)',
  G4: 'G4',
  G9: 'G9',
  G13: 'G13 (трубчатый)',
  GU10: 'GU10',
  'GU5.3': 'GU5.3',
};

/** Человекочитаемые подписи статусов заказа — для экрана подтверждения после оформления. */
export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  pending: 'Оформляется',
  failed: 'Не удалось оформить',
  new: 'Принят',
  paid: 'Оплачен',
  shipped: 'Отправлен',
  completed: 'Выполнен',
  cancelled: 'Отменён',
};

/** Человекочитаемые подписи ролей администратора — для шапки админки. */
export const ROLE_LABELS: Record<RoleName, string> = {
  superadmin: 'Суперадмин',
  manager: 'Менеджер',
  moderator: 'Модератор',
};
