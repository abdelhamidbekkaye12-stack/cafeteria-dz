from django.core.exceptions import ValidationError
from django.db import transaction

from catalogue.models import Produit

from .models import LigneVente, Vente


@transaction.atomic
def enregistrer_vente(session, articles, montant_recu):
    """
    Enregistre une vente et ses lignes, puis la renvoie.

    articles : liste de couples (identifiant du produit, quantité),
               par exemple [(1, 2), (5, 1)] pour 2 × produit n°1 et 1 × produit n°5.

    Le total est TOUJOURS calculé ici, à partir des prix de la base de données.
    """
    session.refresh_from_db()
    if not session.est_ouverte:
        raise ValidationError("La session de caisse est fermée.")
    if not articles:
        raise ValidationError("La vente ne contient aucun article.")

    lignes = []
    total = 0
    for produit_id, quantite in articles:
        if quantite < 1:
            raise ValidationError("La quantité doit être d'au moins 1.")
        try:
            produit = Produit.objects.get(pk=produit_id, en_vente=True)
        except Produit.DoesNotExist:
            raise ValidationError(f"Le produit n°{produit_id} n'est pas en vente.")

        lignes.append(LigneVente(produit=produit, quantite=quantite, prix_unitaire=produit.prix))
        total += quantite * produit.prix

    if montant_recu < total:
        raise ValidationError(
            f"Montant reçu insuffisant : {montant_recu} DA pour un total de {total} DA."
        )

    vente = Vente.objects.create(session=session, total=total, montant_recu=montant_recu)
    for ligne in lignes:
        ligne.vente = vente
    LigneVente.objects.bulk_create(lignes)
    return vente