from httpx_sse import SSEError


class ITDError(Exception):
    messages = {
        'Session not found': 'Такого refresh токена не существует.',
        'Refresh token not found': 'Refresh токен не указан или равен пустой строке',
        'Session revoked': 'Refresh токен отозван',
        'Password requirement not met': "Пароль не соответствует требованиям",
        'New password must be different from current password': "Новый пароль должен отличать от предыдущего",
        'Incorrect old password': 'Старый пароль указан неверно',
        'Недопустимый тип файла': 'Недопустимый тип файла',
        'File not found': "Файл не найден",
        'File not found or access denied': 'Файл не надйне или нет прав на изменение',
        'Post not found': "Пост не существует (или удалён)",
        'Not allowed to delete this post': "Нет прав для удаления поста",
        'Not allowed to restore this post': "Нет прав для восстановления поста",
        'Can only pin your own posts or posts on your wall': 'Можно прикреплять посты только на своей стене',
        'This post is not pinned': 'Пост не прикреплён',
        'Already reposted this post': 'Нельзя репостнуть пост два раза',
        'Cannot repost your own post': "Нельзя репостить свои посты",
        'User not found': 'Пользователь не найден',
        'Content or attachments required': 'Необходимы content или attachments, нельзя создать пустой пост',
        'Maximum 10 attachments allowed per post': 'К посту можно прикрепить максимум 10 файлов',
        'Not allowed to edit this post': "Нет прав для редактирования этого поста",
        'Comment not found': 'Комментарий не найден',
        'Not allowed to delete this comment': 'нет прав на удаление комментария',
        'Rate limit exceeded': 'Слишком много запросов',
        'Content, attachments or poll required': "Нельзя создать пустой пост",
        'Already following this user': 'Уже подписаны на этого пользователя',
        'Session expired': 'Токен истёк'
    }

    def __init__(self, code: str, message: str):
        self.message = message
        self.code = code

    def __str__(self):
        return f"code='{self.code}', message='{self.messages.get(self.message, self.message)}'"


class UnauthorizedError(ITDError):
    code = "UNAUTHORIZED"
    message = "Ошибка авторизации (просрочен access токен)"


class ServerError(ITDError):
    code = "SERVER_ERROR"
    message = "Сервер временно недоступен"


class GatewayTimeOutError(ITDError):
    code = "GET_WAY"


class UnknowError(ITDError):
    code = "UNKNOWN_ERROR"


class Error429(ITDError):
    code = "Too Many Requests"


class RateLimitError(ITDError):
    code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, code: str, message: str, retry_after: int):
        super().__init__(code, message)
        self.retry_after = retry_after

    def __str__(self):
        return super().__str__() + f", retry_after={self.retry_after}"


class TokenNotFoundError(ITDError):
    code = "SESSION_NOT_FOUND"


class TokenRevokedError(ITDError):
    code = "SESSION_REVOKED"


class TokenExpiredError(ITDError):
    code = "SESSION_EXPIRED"


class TokenMissingError(ITDError):
    code = "REFRESH_TOKEN_MISSING"


class SomePasswordError(ITDError):
    code = "SAME_PASSWORD"


class InvalidPasswordError(ITDError):
    code = "INVALID_PASSWORD"


class InvalidOldPasswordError(ITDError):
    code = "INVALID_OLD_PASSWORD"


class UploadError(ITDError):
    code = "UPLOAD_ERROR"


class ParamsValidationError(ITDError):
    def __init__(self, type: str, on: str, found: dict[str, str]):
        self.type = type
        self.on = on
        self.found = found

    def __str__(self):
        return f"type: {self.type}, on: {self.on}, found: {self.found}"


class ValidationError(ITDError):
    code = "VALIDATION_ERROR"


class TooLargeError(ITDError):
    code = "413"


class NotAllowedError(ITDError):
    code = "403"


class NotFoundError(ITDError):
    code = "NOT_FOUND"


class ForbiddenError(ITDError):
    code = "FORBIDDEN"


class NotPinedError(ITDError):
    code = "NOT_PINNED"


class ConflictError(ITDError):
    code = "CONFLICT"


class UserBlockedError(ITDError):
    code = "USER_BLOCKED"


itd_exceptions = [
    TokenNotFoundError,
    TokenRevokedError,
    TokenMissingError,
    UnauthorizedError,
    NotFoundError,
    InvalidPasswordError,
    InvalidOldPasswordError,
    InvalidOldPasswordError,
    SomePasswordError,
    ForbiddenError,
    ValidationError,
    NotPinedError,
    ConflictError,
    RateLimitError,
    UnknowError,
    ServerError,
    UploadError,
    UserBlockedError,
    TokenExpiredError
]

itd_codes = {}
for exception in itd_exceptions:
    itd_codes[exception.code] = exception
