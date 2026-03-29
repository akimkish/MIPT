# middleware.py
import logging
import functools
import datetime

# Настройка логирования (можно вывести в файл или в консоль)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_call(func):
    """Декоратор для логирования вызовов функций и их аргументов."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Подготавливаем информацию о вызове
        func_name = func.__name__
        # Собираем аргументы в удобный для логирования формат
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        
        logger.info(f"Вызов функции {func_name}({signature})")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"Функция {func_name} завершилась успешно. Результат: {result!r}")
            return result
        except (ValueError, KeyError) as e:
            # Логируем ошибку и пробрасываем исключение дальше
            logger.error(f"Функция {func_name} вызвала исключение {type(e).__name__}: {e}")
            raise
        except Exception as e:
            # Для других исключений просто логируем (без проброса? но по условию не требуется)
            logger.error(f"Функция {func_name} вызвала непредвиденное исключение {type(e).__name__}: {e}")
            raise
    
    return wrapper