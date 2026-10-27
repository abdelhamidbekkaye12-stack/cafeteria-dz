from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from .models import Categorie, Produit


class CatalogueTests(TestCase):
    """Vérifie les règles de protection du catalogue."""

    def setUp(self):
        self.boissons = Categorie.objects.create(nom="Boissons chaudes")

    def test_produit_normal_accepte(self):
        cafe = Produit.objects.create(nom="Café", categorie=self.boissons, prix=80)
        self.assertEqual(cafe.prix, 80)

    def test_prix_zero_refuse_par_la_base(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Produit.objects.create(nom="Café", categorie=self.boissons, prix=0)

    def test_categorie_avec_produits_non_supprimable(self):
        Produit.objects.create(nom="Café", categorie=self.boissons, prix=80)
        with self.assertRaises(ProtectedError):
            self.boissons.delete()

# Create your tests here.
