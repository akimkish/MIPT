#!/usr/bin/env bash
#
# Создаёт структуру папок и пустые файлы фронтенда для Lamp Store.
#
# ЗАПУСКАТЬ ИЗ КОРНЯ РЕПОЗИТОРИЯ (там, где лежит папка frontend/,
# на одном уровне с products_service/, orders_service/, admin_service/):
#
#   ./create_frontend_structure.sh
#
# Скрипт идемпотентен: mkdir -p и `touch` не портят уже существующие
# файлы (touch только обновит mtime), повторный запуск безопасен.

set -euo pipefail

# Проверка, что скрипт запущен из корня проекта, а не откуда попало —
# иначе структура создастся не там и придётся вручную переносить.
if [[ ! -d "frontend" ]]; then
  echo "Ошибка: папка 'frontend/' не найдена в текущей директории." >&2
  echo "Запустите скрипт из корня репозитория lamp-store/." >&2
  exit 1
fi

SRC="frontend/src"

# --- Каталоги -----------------------------------------------------------

mkdir -p \
  "$SRC/app" \
  "$SRC/api" \
  "$SRC/types" \
  "$SRC/lib" \
  "$SRC/features/catalog/hooks" \
  "$SRC/features/catalog/components" \
  "$SRC/features/catalog/pages" \
  "$SRC/features/product-detail/hooks" \
  "$SRC/features/product-detail/components" \
  "$SRC/features/product-detail/pages" \
  "$SRC/features/cart/hooks" \
  "$SRC/features/cart/components" \
  "$SRC/features/checkout/hooks" \
  "$SRC/features/checkout/pages" \
  "$SRC/features/admin-auth/hooks" \
  "$SRC/features/admin-auth/pages" \
  "$SRC/features/admin-products/hooks" \
  "$SRC/features/admin-products/pages" \
  "$SRC/features/admin-catalog-refs/hooks" \
  "$SRC/features/admin-catalog-refs/pages" \
  "$SRC/features/admin-reviews/hooks" \
  "$SRC/features/admin-reviews/pages" \
  "$SRC/features/admin-promos/hooks" \
  "$SRC/features/admin-promos/pages" \
  "$SRC/features/admin-orders/hooks" \
  "$SRC/features/admin-orders/pages" \
  "$SRC/features/admin-management/hooks" \
  "$SRC/features/admin-management/pages"

# --- app/ -----------------------------------------------------------------

touch \
  "$SRC/app/App.tsx" \
  "$SRC/app/providers.tsx" \
  "$SRC/app/router.tsx"

# --- api/ -------------------------------------------------------------------

touch \
  "$SRC/api/httpClient.ts" \
  "$SRC/api/productsApi.ts" \
  "$SRC/api/ordersApi.ts" \
  "$SRC/api/adminApi.ts" \
  "$SRC/api/errors.ts"

# --- types/ -----------------------------------------------------------------

touch \
  "$SRC/types/common.ts" \
  "$SRC/types/enums.ts" \
  "$SRC/types/category.ts" \
  "$SRC/types/manufacturer.ts" \
  "$SRC/types/product.ts" \
  "$SRC/types/review.ts" \
  "$SRC/types/promo.ts" \
  "$SRC/types/order.ts" \
  "$SRC/types/admin.ts"

# --- lib/ -------------------------------------------------------------------

touch \
  "$SRC/lib/money.ts" \
  "$SRC/lib/queryKeys.ts" \
  "$SRC/lib/constants.ts"

# --- features/catalog --------------------------------------------------------

touch \
  "$SRC/features/catalog/hooks/useCategories.ts" \
  "$SRC/features/catalog/hooks/useManufacturers.ts" \
  "$SRC/features/catalog/hooks/useProducts.ts"

# --- features/product-detail --------------------------------------------------

touch \
  "$SRC/features/product-detail/hooks/useProduct.ts" \
  "$SRC/features/product-detail/hooks/useProductReviews.ts" \
  "$SRC/features/product-detail/hooks/useCreateReview.ts"

# --- features/cart ------------------------------------------------------------

touch \
  "$SRC/features/cart/cartStore.ts" \
  "$SRC/features/cart/types.ts" \
  "$SRC/features/cart/hooks/useCart.ts"

# --- features/checkout ---------------------------------------------------------

touch \
  "$SRC/features/checkout/hooks/useCreateOrder.ts"

# --- features/admin-auth ----------------------------------------------------------

touch \
  "$SRC/features/admin-auth/authStore.ts" \
  "$SRC/features/admin-auth/hooks/useAdminLogin.ts" \
  "$SRC/features/admin-auth/hooks/useCurrentAdmin.ts"

# --- features/admin-products --------------------------------------------------------

touch \
  "$SRC/features/admin-products/hooks/useAdminProducts.ts" \
  "$SRC/features/admin-products/hooks/useCreateProduct.ts" \
  "$SRC/features/admin-products/hooks/useUpdateProduct.ts" \
  "$SRC/features/admin-products/hooks/useDeactivateProduct.ts"

# --- features/admin-catalog-refs -----------------------------------------------------

touch \
  "$SRC/features/admin-catalog-refs/hooks/useAdminCategories.ts" \
  "$SRC/features/admin-catalog-refs/hooks/useAdminManufacturers.ts"

# --- features/admin-reviews -----------------------------------------------------------

touch \
  "$SRC/features/admin-reviews/hooks/usePendingReviews.ts" \
  "$SRC/features/admin-reviews/hooks/useApproveReview.ts" \
  "$SRC/features/admin-reviews/hooks/useDeleteReview.ts"

# --- features/admin-promos -------------------------------------------------------------

touch \
  "$SRC/features/admin-promos/hooks/useAdminPromos.ts" \
  "$SRC/features/admin-promos/hooks/useCreatePromo.ts" \
  "$SRC/features/admin-promos/hooks/useUpdatePromo.ts" \
  "$SRC/features/admin-promos/hooks/useDeactivatePromo.ts"

# --- features/admin-orders --------------------------------------------------------------

touch \
  "$SRC/features/admin-orders/hooks/useAdminOrders.ts" \
  "$SRC/features/admin-orders/hooks/useOrder.ts" \
  "$SRC/features/admin-orders/hooks/useUpdateOrderStatus.ts"

# --- features/admin-management -----------------------------------------------------------

touch \
  "$SRC/features/admin-management/hooks/useAdmins.ts" \
  "$SRC/features/admin-management/hooks/useCreateAdmin.ts" \
  "$SRC/features/admin-management/hooks/useDeactivateAdmin.ts" \
  "$SRC/features/admin-management/hooks/useChangeAdminRole.ts"

echo "Структура фронтенда создана в: $SRC"
find "$SRC" -type f | sort