class MyError(Exception):
    """Родительский класс ошибок."""

    def __init__(self, *args: object) -> None:
        """Инициализирует поле message."""
        if args:
            self.message = args[0]
        else:
            self.message = None


class EnvironmentError(MyError):
    """Исключение, вызываемое при неполном окружении."""

    def __str__(self) -> str:
        """В зависимости от значения поля message возвращает строку."""
        if self.message:
            return 'EnvironmentError: {0}'.format(self.message)
        else:
            return 'EnvironmentError: Something is wrong with the environment!'


class IncorrectKey(MyError):
    """Исключение, вызываемое при неверном ключе."""

    def __str__(self) -> str:
        """В зависимости от значения поля message возвращает строку."""
        if self.message:
            return 'IncorrectKey: {0}'.format(self.message)
        else:
            return 'IncorrectKey: There is no such key'


class APIError(MyError):
    """Исключение, вызываемое при неверном ответе API."""

    def __str__(self) -> str:
        """В зависимости от значения поля message возвращает строку."""
        if self.message:
            return 'APIError: {0}'.format(self.message)
        else:
            return 'APIError: Unnoun API error'
