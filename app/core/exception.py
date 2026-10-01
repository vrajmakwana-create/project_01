from fastapi import status as http_status
from app.core.message import ErrorMessage


class ServerException(Exception):

    def __init__(
        self,
        message: str = ErrorMessage.INTERNAL_SERVER_ERROR,
        status_code: int = http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = str(message)
        self.status_code = status_code
        super().__init__(message)
