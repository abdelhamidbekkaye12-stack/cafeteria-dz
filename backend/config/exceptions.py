from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """Transforme les erreurs métier de Django en réponses 400 lisibles."""
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError({"detail": " ".join(exc.messages)})
    return drf_exception_handler(exc, context)