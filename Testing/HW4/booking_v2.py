import datetime
from Testing.HW4.midlleware import function_logger

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
    print("=== Тестирование успешного создания брони ===")
    try:
        booking = create_booking(event_id=1, user_id=101)
        print("Created booking:", booking)

        print("\n=== Тестирование получения брони ===")
        retrieved = get_booking(booking["booking_id"])
        print("Retrieved booking:", retrieved)
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Тестирование ошибки создания брони (несуществующий event_id) ===")
    try:
        create_booking(event_id=999, user_id=102)
    except ValueError as e:
        print(f"Caught expected error: {e}")

    print("\n=== Тестирование ошибки получения брони (несуществующий booking_id) ===")
    try:
        get_booking("invalid_booking_id")
    except KeyError as e:
        print(f"Caught expected error: {e}")
