from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Employe
from .serializers import ConnexionPinSerializer, EmployeListeSerializer


class EmployesConnexionView(generics.ListAPIView):
    """Les employés qui peuvent se connecter à la caisse."""

    permission_classes = [AllowAny]
    serializer_class = EmployeListeSerializer

    def get_queryset(self):
        return (
            Employe.objects.filter(is_active=True)
            .exclude(pin_hash="")
            .order_by("first_name", "username")
        )


class ConnexionPinView(APIView):
    """Vérifie le PIN d'un employé et lui remet un jeton."""

    permission_classes = [AllowAny]

    def post(self, request):
        donnees = ConnexionPinSerializer(data=request.data)
        donnees.is_valid(raise_exception=True)

        employe = Employe.objects.filter(
            pk=donnees.validated_data["employe_id"], is_active=True
        ).first()

        if employe is None or not employe.verifier_pin(donnees.validated_data["pin"]):
            if employe is not None and employe.pin_verrouille:
                return Response(
                    {"detail": "Compte verrouillé : demandez au gérant de redéfinir votre PIN."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(
                {"detail": "Employé ou PIN incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jeton, _ = Token.objects.get_or_create(user=employe)
        return Response({"token": jeton.key, "employe": EmployeListeSerializer(employe).data})

# Create your views here.
