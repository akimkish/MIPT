import { create } from 'zustand';

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  clearToken: () => void;
}

/**
 * Хранит JWT администратора только в памяти (НЕ persist, НЕ localStorage).
 *
 * Осознанное упрощение в другую сторону от типичного продакшена: в проде
 * для JWT часто делают httpOnly cookie + refresh-токен, чтобы защититься
 * от кражи токена через XSS. Здесь токен живёт только в памяти вкладки —
 * админ разлогинивается при обновлении страницы, зато не нужно поднимать
 * httpOnly cookie между тремя разными origin'ами ради учебного проекта.
 * Согласуется с TTL access-токена в 30 минут и known_limitations #3.
 */
export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  clearToken: () => set({ token: null }),
}));
