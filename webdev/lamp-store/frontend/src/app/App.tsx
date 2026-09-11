import { AppRouter } from './router';
import { Providers } from './providers';

/**
 * Корневой компонент приложения: провайдеры верхнего уровня + роутинг.
 *
 * Временный `useState`-переключатель между каталогом и карточкой товара
 * (из предыдущего шага) заменён на настоящие маршруты `AppRouter` —
 * `CatalogPage`/`ProductDetailPage` при этом не изменились, они были
 * спроектированы без прямой зависимости от роутера именно ради такой
 * безболезненной замены.
 */
export function App() {
  return (
    <Providers>
      <AppRouter />
    </Providers>
  );
}
