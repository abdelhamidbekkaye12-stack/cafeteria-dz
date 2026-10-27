from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Sum
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
    models.CheckConstraint(
                condition=(
                    models.Q(fermee_le__isnull=True)
                    | (
                        models.Q(montant_compte__isnull=False)
                        & models.Q(montant_attendu__isnull=False)
                        & models.Q(ecart__isnull=False)
                    )
                ),
                name="session_fermee_avec_montants",
            ),
            
    models.CheckConstraint(
                condition=(
                    models.Q(fermee_le__isnull=True)
                    | models.Q(ecart=models.F("montant_compte") - models.F("montant_attendu"))
                ),
                name="session_ecart_coherent",
            ),

    def __str__(self):
        etat = "ouverte" if self.est_ouverte else "fermée"
        ouverture = timezone.localtime(self.ouverte_le)
        return f"Session de {self.employe} du {ouverture:%d/%m/%Y %H:%M} ({etat})"

    @property
    def est_ouverte(self):
        return self.fermee_le is None
    def calculer_montant_attendu(self):
        """Fond initial + ventes non annulées − sorties."""
        ventes = self.ventes.filter(annulee=False).aggregate(somme=Sum("total"))["somme"] or 0
        sorties = self.sorties.aggregate(somme=Sum("montant"))["somme"] or 0
        return self.fond_initial + ventes - sorties
class Vente(models.Model):
    """Un ticket de caisse. Jamais supprimé : il peut seulement être annulé."""

    session = models.ForeignKey(
        SessionCaisse,
        on_delete=models.PROTECT,
        related_name="ventes",
        verbose_name="session de caisse",
    )
    cree_le = models.DateTimeField("créée le", auto_now_add=True)
    total = models.PositiveIntegerField("total (DA)")
    montant_recu = models.PositiveIntegerField("montant reçu (DA)")

    # Annulation (réservée au gérant, motif obligatoire)
    annulee = models.BooleanField("annulée", default=False)
    annulee_le = models.DateTimeField("annulée le", null=True, blank=True)
    annulee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ventes_annulees",
        verbose_name="annulée par",
    )
    motif_annulation = models.TextField("motif d'annulation", blank=True)

    class Meta:
        verbose_name = "vente"
        verbose_name_plural = "ventes"
        ordering = ["-cree_le"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total__gte=1),
                name="vente_total_au_moins_1_da",
            ),
            models.CheckConstraint(
                condition=models.Q(montant_recu__gte=models.F("total")),
                name="vente_montant_recu_suffisant",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(annulee=False)
                    | (
                        models.Q(annulee_par__isnull=False)
                        & models.Q(annulee_le__isnull=False)
                        & ~models.Q(motif_annulation="")
                    )
                ),
                name="vente_annulation_complete",
            ),
        ]

    def __str__(self):
        creation = timezone.localtime(self.cree_le)
        return f"Vente n°{self.pk} du {creation:%d/%m/%Y %H:%M} ({self.total} DA)"

    @property
    def employe(self):
        return self.session.employe

    @property
    def rendu(self):
        return self.montant_recu - self.total


class LigneVente(models.Model):
    """Un article d'un ticket : « 2 × Café express à 80 DA »."""

    vente = models.ForeignKey(
        Vente,
        on_delete=models.PROTECT,
        related_name="lignes",
        verbose_name="vente",
    )
    produit = models.ForeignKey(
        "catalogue.Produit",
        on_delete=models.PROTECT,
        related_name="lignes_vente",
        verbose_name="produit",
    )
    quantite = models.PositiveSmallIntegerField("quantité")
    prix_unitaire = models.PositiveIntegerField("prix unitaire (DA)")

    class Meta:
        verbose_name = "ligne de vente"
        verbose_name_plural = "lignes de vente"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantite__gte=1),
                name="ligne_quantite_au_moins_1",
            ),
            models.CheckConstraint(
                condition=models.Q(prix_unitaire__gte=1),
                name="ligne_prix_au_moins_1_da",
            ),
        ]

    def __str__(self):
        return f"{self.quantite} × {self.produit.nom} à {self.prix_unitaire} DA"

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire
# Create your models here.
class SortieCaisse(models.Model):
    """De l'argent qui quitte le tiroir : livreur payé, achat urgent…"""

    session = models.ForeignKey(
        SessionCaisse,
        on_delete=models.PROTECT,
        related_name="sorties",
        verbose_name="session de caisse",
    )
    montant = models.PositiveIntegerField("montant (DA)")
    motif = models.CharField("motif", max_length=255)
    cree_le = models.DateTimeField("déclarée le", auto_now_add=True)

    class Meta:
        verbose_name = "sortie de caisse"
        verbose_name_plural = "sorties de caisse"
        ordering = ["-cree_le"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(montant__gte=1),
                name="sortie_montant_au_moins_1_da",
            ),
            models.CheckConstraint(
                condition=~models.Q(motif=""),
                name="sortie_motif_obligatoire",
            ),
        ]

    def __str__(self):
        return f"Sortie de {self.montant} DA : {self.motif}"