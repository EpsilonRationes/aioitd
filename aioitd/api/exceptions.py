class TokenNotFoundError(ValueError):
    def __init__(self, token: str) -> None:
        self.token = token

    def __str__(self):
        return f"Токена {self.token} не существует"


class TokenRevokedError(ValueError):
    def __init__(self, token: str) -> None:
        self.token = token

    def __str__(self) -> str:
        return f"Токен {self.token} отозван"


class MissingTokenError(ValueError):
    def __str__(self) -> str:
        return f"Токен не указан (равен пустой строке)"


class ITDError(Exception):
    def __init__(self, code: str, message: str):
        self.message = message
        self.code = code

    def __str__(self):
        return f"ITDError: code={self.code}, message={self.message}"


class UnauthorizedError(ITDError):
    def __str__(self):
        return f"Не авторизован"


class NotFoundError(ValueError):
    ...


class InvalidPasswordError(ValueError):
    def __str__(self) -> str:
        return "Пароль не подходит под условия"


class InvalidOldPasswordError(ValueError):
    def __str__(self) -> str:
        return "Указан неверный старый пароль"


class SomePasswordError(ValueError):
    def __str__(self) -> str:
        return "Новый пароль должен отличать от старого"


class FileNotFound(ValueError):
    def __str__(self):
        return f"Файл не найден, или нет прав доступа к нему"


class ForbiddenError(ValueError):
    ...


class NotPinedError(Exception):
    def __set__(self):
        return f"Пост не прикреплён"


class ConflictError(ValueError): ...
