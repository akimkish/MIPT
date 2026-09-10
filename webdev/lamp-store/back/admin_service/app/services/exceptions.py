class ServiceError(Exception):
    pass


class NotFoundError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class AuthenticationError(ServiceError):
    pass


class AccountLockedError(ServiceError):
    pass


class InactiveAccountError(ServiceError):
    pass


class PermissionDeniedError(ServiceError):
    pass
