class StudyBuddyException(Exception):
    pass


class ValidationError(StudyBuddyException):
    pass


class NotFoundException(StudyBuddyException):
    pass


NotFoundError = NotFoundException


class FileProcessingError(StudyBuddyException):
    pass


class LLMProviderError(StudyBuddyException):
    pass


class VectorStoreError(Exception):
    pass


class DocumentProcessingError(Exception):
    pass


class DatabaseError(StudyBuddyException):
    pass


class AuthenticationError(StudyBuddyException):
    pass
