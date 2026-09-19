class ProductNotFoundError(Exception):
    pass

class InsufficientStockError(Exception):
    pass

class DuplicateRequestError(Exception):
    pass

class InvalidAudioError(Exception):
    pass

class SpeechProviderError(Exception):
    pass

class UnknownIntentError(Exception):
    pass

class ConfirmationExpiredError(Exception):
    pass

class AuthenticationError(Exception):
    pass

class AuthorizationError(Exception):
    pass

class ValidationError(Exception):
    pass

