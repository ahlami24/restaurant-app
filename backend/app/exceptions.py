class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""


class ConflictError(Exception):
    """Raised when an operation conflicts with the resource's current state."""


class ForbiddenError(Exception):
    """Raised when the current actor is not allowed to perform an action."""