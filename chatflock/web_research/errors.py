class TransientHTTPError(Exception):
    def __init__(self, http_status_code: int, message: str):
        self.http_status_code = http_status_code
        self.message = message


class NonTransientHTTPError(Exception):
    def __init__(self, http_status_code: int, message: str):
        self.http_status_code = http_status_code
        self.message = message
