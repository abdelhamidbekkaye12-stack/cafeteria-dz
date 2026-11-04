from rest_framework import serializers

from .models import PIN_LONGUEUR, Employe


class EmployeListeSerializer(serializers.ModelSerializer):
    """Un employé tel qu'il apparaît sur l'écran de connexion."""

    nom = serializers.SerializerMethodField()

    class Meta:
        model = Employe
        fields = ["id", "nom"]

    def get_nom(self, employe):
        return employe.get_full_name() or employe.username


class ConnexionPinSerializer(serializers.Serializer):
    """Les données envoyées par l'écran pour se connecter."""

    employe_id = serializers.IntegerField()
    pin = serializers.CharField(max_length=PIN_LONGUEUR)