from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SessionCaisse
from .serializers import (
    ClotureSerializer,
    NouvelleVenteSerializer,
    OuvertureSerializer,
    SessionSerializer,
    SortieSerializer,
    VenteSerializer,
)
from .services import cloturer_session, declarer_sortie, enregistrer_vente, ouvrir_session


def session_ouverte_de(employe):
    """Renvoie la session ouverte de l'employé, ou une erreur 404."""
    session = SessionCaisse.objects.filter(employe=employe, fermee_le__isnull=True).first()
    if session is None:
        raise NotFound("Aucune session de caisse ouverte.")
    return session


def lire(serializer_class, request):
    """Vérifie les données reçues et les renvoie, ou une erreur 400."""
    donnees = serializer_class(data=request.data)
    donnees.is_valid(raise_exception=True)
    return donnees.validated_data


class SessionCouranteView(APIView):
    def get(self, request):
        session = session_ouverte_de(request.user)
        return Response(SessionSerializer(session).data)


class OuvrirSessionView(APIView):
    def post(self, request):
        donnees = lire(OuvertureSerializer, request)
        session = ouvrir_session(request.user, donnees["fond_initial"])
        return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)


class VenteView(APIView):
    def post(self, request):
        donnees = lire(NouvelleVenteSerializer, request)
        articles = [(a["produit_id"], a["quantite"]) for a in donnees["articles"]]
        vente = enregistrer_vente(
            session_ouverte_de(request.user), articles, donnees["montant_recu"]
        )
        return Response(VenteSerializer(vente).data, status=status.HTTP_201_CREATED)


class SortieView(APIView):
    def post(self, request):
        donnees = lire(SortieSerializer, request)
        declarer_sortie(session_ouverte_de(request.user), donnees["montant"], donnees["motif"])
        return Response({"detail": "Sortie enregistrée."}, status=status.HTTP_201_CREATED)


class CloturerSessionView(APIView):
    def post(self, request):
        donnees = lire(ClotureSerializer, request)
        cloturer_session(session_ouverte_de(request.user), donnees["montant_compte"])
        return Response({"detail": "Caisse clôturée. Merci !"})

# Create your views here.
