class APIError(Exception):
    """Исключение, вызываемое при неверном ответе API."""

    def __str__(self) -> str:
        """В зависимости от значения поля message возвращает строку."""
        if self.message:
            return 'APIError: {0}'.format(self.message)
