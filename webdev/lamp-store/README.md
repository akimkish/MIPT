# Lamp Store

## Архитектура

```
lamp-store/
├── products_service/   FastAPI — каталог, категории, производители, промо, отзывы
├── orders_service/      FastAPI — заказы, вызывает products_service по HTTP
├── admin_service/        FastAPI — администраторы, аутентификация (JWT), аудит
└── frontend/               React + TypeScript SPA — витрина и (в будущем) админка
```

## Запуск бэкенда

```bash
cd lamp-store/
cp products_service/.env.example products_service/.env
cp orders_service/.env.example orders_service/.env
cp admin_service/.env.example admin_service/.env
```

Откройте `admin_service/.env` и задайте `FIRST_ADMIN_EMAIL` /
`FIRST_ADMIN_PASSWORD` — первый администратор (`role_name=superadmin`)
создаётся автоматически при первом старте, если таблица `admins` пуста.

```bash
docker compose up --build
```

## Запуск фронтенда

```bash
cd frontend/
npm install
npm install @tanstack/react-query zustand react-router-dom
npm install vite --save-dev
npm install --save-dev @vitejs/plugin-react
npm install @types/node --save-dev
```

Запуск дев-сервера:

```bash
npm run dev
```
