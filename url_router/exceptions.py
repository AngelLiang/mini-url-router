

class ValidationError(ValueError):
    pass


class HTTPException(Exception):
    pass


class RoutingException(Exception):
    pass


class RequestRedirect(HTTPException, RoutingException):
    pass


class NotFound(HTTPException):
    pass


class MethodNotAllowed(HTTPException):
    pass


class BuildError(RoutingException, LookupError):
    pass


class RequestSlash(RoutingException):
    pass
