import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

/**
 * Единственный QueryClient на всё приложение.
 *
 * Создаётся модульной константой, а не через `useState` внутри
 * компонента — иначе он пересоздавался бы при каждом ре-рендере
 * `Providers` вместе со всем накопленным кэшем.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // дефолт React Query — 3 повтора — слишком долго держит спиннер при реальном сбое
      staleTime: 30 * 1000,
    },
  },
});

interface ProvidersProps {
  children: ReactNode;
}

/** Оборачивает приложение всеми контекст-провайдерами верхнего уровня. */
export function Providers({ children }: ProvidersProps) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
