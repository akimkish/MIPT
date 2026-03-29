import functools
import logging
import datetime

# Настройка системы логирования в файл
logging.basicConfig(
    level=logging.INFO,
    filename="logging.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Cоздаем экземпляр объекта логгера
logger = logging.getLogger(__name__)


def function_logger(service_name: str):
    # Функция-декоратор для логирования вызовов функций
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Логируем вызов функции и аргументы
            func_args = []
            if args:
                func_args.extend(map(str, args))
            if kwargs:
                func_args.extend([f"{k}={v}" for k, v in kwargs.items()])
            args_str = ", ".join(func_args)
            logger.info(f"[{service_name}] calls {func.__name__}({args_str})")
            # Логируем успешный вызов функции или ошибку
            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"[{service_name}] {func.__name__} completed successfully. Result: {result}"
                )
                return result
            except (ValueError, KeyError) as e:
                error_msg = f"[{service_name}] {func.__name__} failed with {type(e).__name__}: {str(e)}"
                logger.error(error_msg)
                raise
            except Exception as e:
                error_msg = f"[{service_name}] {func.__name__} failed with unexpected error {type(e).__name__}: {str(e)}"
                logger.error(error_msg)
                raise

        return wrapper

    return decorator


# Упрощенная «база» мероприятий
EVENTS_DB = {
    1: {
        "title": "Football Match",
        "available_seats": 10,
        "date": datetime.date(2025, 7, 1),
    },
    2: {
        "title": "Basketball Playoffs",
        "available_seats": 5,
        "date": datetime.date(2025, 7, 2),
    },
    3: {
        "title": "Tennis Open",
        "available_seats": 3,
        "date": datetime.date(2025, 7, 3),
    },
}

# Упрощённая «база» бронирований (хранилище в памяти)
BOOKINGS_DB = {}


@function_logger("Booking")
def create_booking(event_id: int, user_id: int) -> dict:
    """
    Создаёт бронь на мероприятие event_id для пользователя user_id.
    Возвращает словарь с данными о брони или выбрасывает ValueError при ошибках.
    """
    if event_id not in EVENTS_DB:
        raise ValueError(f"Event with id={event_id} does not exist.")

    event_info = EVENTS_DB[event_id]
    if event_info["available_seats"] <= 0:
        raise ValueError("No available seats.")

    # Условная логика — уменьшаем количество доступных мест
    event_info["available_seats"] -= 1
    # Генерируем booking_id (например, текущее время + user_id)
    booking_id = f"{int(datetime.datetime.now().timestamp())}_{user_id}"

    BOOKING_DATA = {
        "booking_id": booking_id,
        "event_id": event_id,
        "user_id": user_id,
        "title": event_info["title"],
        "date": event_info["date"],
        "created_at": datetime.datetime.now(),
    }
    # Сохраняем в словарь (как базу данных)
    BOOKINGS_DB[booking_id] = BOOKING_DATA

    return BOOKING_DATA


@function_logger("Booking")
def get_booking(booking_id: str) -> dict:
    """
    Возвращает данные о конкретной брони по booking_id.
    Поднимает KeyError, если брони нет.
    """
    return BOOKINGS_DB[booking_id]


# Пример использования (для теста)
if __name__ == "__main__":
    # Пробуем создать бронь (успешное выполнение)
    try:
        booking = create_booking(event_id=1, user_id=101)
        print("Created booking:", booking)
    except Exception as e:
        print(f"Error: {e}")
    # Пробуем получить бронь (успешное выполнение)
    try:
        retrieved = get_booking(booking["booking_id"])
        print("Retrieved booking:", retrieved)
    except Exception as e:
        print(f"Error: {e}")

    # Пробуем создать бронь (ошибка - несуществующий event_id)
    try:
        e_booking = create_booking(event_id=999, user_id=102)
    except ValueError as e:
        print(f"Error: {e}")

    # Пробуем создать бронь (ошибка - несуществующий booking_id)
    try:
        e_retrieved = get_booking("invalid_booking_id")
    except KeyError as e:
        print(f"Error: {e}")
