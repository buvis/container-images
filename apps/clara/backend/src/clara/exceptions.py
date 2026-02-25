import uuid


class AppError(Exception):
    pass


class NotFoundError(AppError):
    def __init__(self, entity: str, id: uuid.UUID) -> None:
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} {id} not found")


class ForbiddenError(AppError):
    pass


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class InvalidCredentialsError(AppError):
    pass
