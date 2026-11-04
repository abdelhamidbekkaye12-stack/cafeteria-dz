from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from caisse.models import SessionCaisse, Vente
from caisse.serializers import VenteSerializer
from caisse.services import annuler_vente
from comptes.permissions import EstGerant

from .serializers import EcartEmployeSerializer, SessionGestionSerializer

Employe = get_user_model()


class SessionsGestionView(generics.ListAPIView):
    """Toutes les sessions de caisse, avec leurs écarts."""

    permission_classes = [EstGerant]
    serializer_class = SessionGestionSerializer
    queryset = SessionCaisse.objects.select_related("employe")


class EcartsParEmployeView(APIView):
    """Écarts cumulés par employé, du plus grand manque au plus grand excédent."""

    permission_classes = [EstGerant]

    def get(self, request):
        clotures = Q(sessions_caisse__fermee_le__isnull=False)
        employes = (
            Employe.objects.annotate(
                nb_sessions=Count("sessions_caisse", filter=clotures),
                nb_sessions_en_moins=Count(
                    "sessions_caisse", filter=Q(sessions_caisse__ecart__lt=0)
                ),
                ecart_total=Coalesce(Sum("sessions_caisse__ecart"), 0),
            )
            .filter(nb_sessions__gt=0)
            .order_by("ecart_total")
        )
        return Response(EcartEmployeSerializer(employes, many=True).data)


class AnnulerVenteView(APIView):
    """Annule une vente de la caisse encore ouverte."""

    permission_classes = [EstGerant]

    def post(self, request, pk):
        vente = get_object_or_404(Vente, pk=pk)
        vente = annuler_vente(vente, request.user, request.data.get("motif", ""))
        return Response(VenteSerializer(vente).data)

# Create your views here.
