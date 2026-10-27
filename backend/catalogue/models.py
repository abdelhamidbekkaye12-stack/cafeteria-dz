from django.core.validators import MinValueValidator
from django.db import models


class Categorie(models.Model):
    """Une famille de produits : boissons chaudes, viennoiseries…"""

    nom = models.CharField("nom", max_length=100, unique=True)
    ordre = models.PositiveSmallIntegerField("ordre d'affichage", default=0)
    active = models.BooleanField("active", default=True)

    class Meta:
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom


class Produit(models.Model):
    """Un article vendu à la caisse."""

    nom = models.CharField("nom", max_length=150)
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name="produits",
        verbose_name="catégorie",
    )
    prix = models.PositiveIntegerField("prix (DA)", validators=[MinValueValidator(1)])
    en_vente = models.BooleanField("en vente", default=True)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)
    modifie_le = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        verbose_name = "produit"
        verbose_name_plural = "produits"
        ordering = ["categorie", "nom"]

    def __str__(self):
        return f"{self.nom} ({self.prix} DA)"

# Create your models here.
