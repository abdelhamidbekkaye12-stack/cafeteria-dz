from rest_framework import serializers

from .models import Produit


class ProduitSerializer(serializers.ModelSerializer):
    """Un produit tel que l'écran de caisse le reçoit."""

    categorie = serializers.StringRelatedField()

    class Meta:
        model = Produit
        fields = ["id", "nom", "categorie", "prix"]