from rest_framework import generics

from .models import Produit
from .serializers import ProduitSerializer


class ProduitsEnVenteView(generics.ListAPIView):
    """Liste des produits que la caisse peut vendre."""

    serializer_class = ProduitSerializer

    def get_queryset(self):
        return Produit.objects.filter(
            en_vente=True, categorie__active=True
        ).select_related("categorie")

# Create your views here.
