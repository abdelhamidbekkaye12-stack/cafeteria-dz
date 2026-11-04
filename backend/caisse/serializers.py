from rest_framework import serializers

from .models import LigneVente, SessionCaisse, Vente

# --- Ce que la tablette envoie ---


class OuvertureSerializer(serializers.Serializer):
    fond_initial = serializers.IntegerField(min_value=0)


class ArticleSerializer(serializers.Serializer):
    produit_id = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)


class NouvelleVenteSerializer(serializers.Serializer):
    articles = ArticleSerializer(many=True, allow_empty=False)
    montant_recu = serializers.IntegerField(min_value=0)


class SortieSerializer(serializers.Serializer):
    montant = serializers.IntegerField(min_value=1)
    motif = serializers.CharField(max_length=255)


class ClotureSerializer(serializers.Serializer):
    montant_compte = serializers.IntegerField(min_value=0)


# --- Ce que la tablette reçoit ---


class SessionSerializer(serializers.ModelSerializer):
    """La session vue par le serveur : jamais le montant attendu."""

    class Meta:
        model = SessionCaisse
        fields = ["id", "fond_initial", "ouverte_le"]


class LigneVenteSerializer(serializers.ModelSerializer):
    produit = serializers.CharField(source="produit.nom")
    sous_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = LigneVente
        fields = ["produit", "quantite", "prix_unitaire", "sous_total"]


class VenteSerializer(serializers.ModelSerializer):
    lignes = LigneVenteSerializer(many=True, read_only=True)
    rendu = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vente
        fields = ["id", "cree_le", "total", "montant_recu", "rendu", "lignes"]