from django.conf import settings
from django.db import models
from django.utils import timezone

class SessionCaisse(models.Model):
    """Le service d'un serveur, de l'ouverture à la clôture de son tiroir."""

    employe = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessions_caisse",
        verbose_name="employé",
    )
    fond_initial = models.PositiveIntegerField("fond de caisse initial (DA)")
    ouverte_le = models.DateTimeField("ouverte le", auto_now_add=True)

    # Rempli à la clôture
    fermee_le = models.DateTimeField("fermée le", null=True, blank=True)
    montant_compte = models.PositiveIntegerField("montant compté (DA)", null=True, blank=True)
    montant_attendu = models.IntegerField("montant attendu (DA)", null=True, blank=True)
    ecart = models.IntegerField("écart (DA)", null=True, blank=True)

    class Meta:
        verbose_name = "session de caisse"
        verbose_name_plural = "sessions de caisse"
        ordering = ["-ouverte_le"]
        constraints = [
            models.UniqueConstraint(
                fields=["employe"],
                condition=models.Q(fermee_le__isnull=True),
                name="une_seule_session_ouverte_par_employe",
            ),
        ]

    def __str__(self):
        etat = "ouverte" if self.est_ouverte else "fermée"
        ouverture = timezone.localtime(self.ouverte_le)
        return f"Session de {self.employe} du {ouverture:%d/%m/%Y %H:%M} ({etat})"

    @property
    def est_ouverte(self):
        return self.fermee_le is None

# Create your models here.
