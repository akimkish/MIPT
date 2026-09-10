import type { SocketType } from '../types/enums';

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
