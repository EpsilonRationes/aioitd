from functools import wraps


def assert_async_raises(exception):
    """Декоратор для проверки исключений в асинхронных функциях"""

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                await func(self, *args, **kwargs)
            except exception:
                return
            else:
                raise AssertionError(f"{exception.__name__} не выброшено")

        return wrapper

    return decorator