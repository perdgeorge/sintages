from enum import StrEnum


class ErrorKind(StrEnum):
    NOT_FOUND = "NotFoundError"
    INTERNAL = "InternalError"
    CONFLICT = "ConflictError"
    VALIDATION = "ValidationError"
    AUTHORIZATION = "AuthorizationError"
