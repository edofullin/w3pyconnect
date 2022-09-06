from lib2to3.pytree import Base


class AuthenticationException(BaseException):
    pass

class UnsupportedLineException(BaseException):
    pass

class NoLinesException(BaseException):
    pass

class RateLimitException(BaseException):
    pass

class InvalidLineException(BaseException):
    pass
