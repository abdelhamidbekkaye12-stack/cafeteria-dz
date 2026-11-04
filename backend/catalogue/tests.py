from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Categorie, Produit
Employe = get_user_model()

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
class ProduitsEnVenteApiTests(APITestCase):
    """Vérifie le guichet /api/catalogue/produits/."""

    def setUp(self):
        self.url = reverse("produits-en-vente")
        self.karim = Employe.objects.create_user(username="karim")

        boissons = Categorie.objects.create(nom="Boissons chaudes")
        viennoiseries = Categorie.objects.create(nom="Viennoiseries", active=False)
        Produit.objects.create(nom="Café express", categorie=boissons, prix=80)
        Produit.objects.create(nom="Café crème", categorie=boissons, prix=120, en_vente=False)
        Produit.objects.create(nom="Croissant", categorie=viennoiseries, prix=60)
    
    def test_inconnu_refuse(self):
        reponse = self.client.get(self.url)
        self.assertEqual(reponse.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employe_connecte_accepte(self):
        self.client.force_authenticate(self.karim)
        reponse = self.client.get(self.url)
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)

    def test_seuls_les_produits_vendables_apparaissent(self):
        self.client.force_authenticate(self.karim)
        noms = [produit["nom"] for produit in self.client.get(self.url).json()]
        self.assertEqual(noms, ["Café express"])

    def test_seuls_les_champs_utiles_sont_envoyes(self):
        self.client.force_authenticate(self.karim)
        produit = self.client.get(self.url).json()[0]
        self.assertEqual(set(produit.keys()), {"id", "nom", "categorie", "prix"})

    def test_creation_de_produit_impossible(self):
        self.client.force_authenticate(self.karim)
        reponse = self.client.post(self.url, {"nom": "Faux café", "prix": 1})