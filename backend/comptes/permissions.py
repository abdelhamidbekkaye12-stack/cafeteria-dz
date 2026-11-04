from rest_framework.permissions import BasePermission

from .models import Employe


class EstGerant(BasePermission):
    """Autorise seulement les employés connectés qui ont le rôle Gérant."""

    message = "Action réservée au gérant."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Employe.Role.GERANT
        )