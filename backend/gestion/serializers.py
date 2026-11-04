from rest_framework import serializers

from caisse.models import SessionCaisse


def nom_employe(employe):
    return employe.get_full_name() or employe.username


class SessionGestionSerializer(serializers.ModelSerializer):
    """La session vue par le gérant : tous les montants."""

    employe = serializers.SerializerMethodField()
    est_ouverte = serializers.BooleanField(read_only=True)

    class Meta:
        model = SessionCaisse
        fields = [
            "id", "employe", "fond_initial", "ouverte_le", "fermee_le",
            "montant_compte", "montant_attendu", "ecart", "est_ouverte",
        ]

    def get_employe(self, session):
        return nom_employe(session.employe)


class EcartEmployeSerializer(serializers.Serializer):
    """Le bilan d'un employé sur toutes ses sessions clôturées."""

    id = serializers.IntegerField()
    nom = serializers.SerializerMethodField()
    nb_sessions = serializers.IntegerField()
    nb_sessions_en_moins = serializers.IntegerField()
    ecart_total = serializers.IntegerField()

    def get_nom(self, employe):
        return nom_employe(employe)