from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from caisse.models import SessionCaisse
from caisse.services import cloturer_session, enregistrer_vente
from catalogue.models import Categorie, Produit

Employe = get_user_model()


class GestionApiTests(APITestCase):
    """Vérifie les actions réservées au gérant."""

    def setUp(self):
        self.gerant = Employe.objects.create_user(username="gerant", role="GERANT")
        self.karim = Employe.objects.create_user(username="karim")
        self.amine = Employe.objects.create_user(username="amine")
        boissons = Categorie.objects.create(nom="Boissons chaudes")
        self.cafe = Produit.objects.create(nom="Café express", categorie=boissons, prix=80)

        self.session = SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)
        self.vente = enregistrer_vente(self.session, [(self.cafe.pk, 2)], montant_recu=200)

    def annuler(self, motif="Erreur de saisie"):
        url = reverse("gestion-annuler-vente", args=[self.vente.pk])
        return self.client.post(url, {"motif": motif}, format="json")

    # --- Accès ---

    def test_serveur_refuse(self):
        self.client.force_authenticate(self.karim)
        reponse = self.client.get(reverse("gestion-sessions"))
        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

    def test_inconnu_refuse(self):
        reponse = self.client.get(reverse("gestion-sessions"))
        self.assertEqual(reponse.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Consultation ---

    def test_gerant_voit_l_ecart(self):
        cloturer_session(self.session, 3000)
        self.client.force_authenticate(self.gerant)
        session = self.client.get(reverse("gestion-sessions")).json()[0]
        self.assertEqual(session["ecart"], -160)

    def test_ecarts_du_pire_au_meilleur(self):
        cloturer_session(self.session, 3000)  # Karim : -160
        session_amine = SessionCaisse.objects.create(employe=self.amine, fond_initial=2000)
        cloturer_session(session_amine, 2050)  # Amine : +50

        self.client.force_authenticate(self.gerant)
        bilan = self.client.get(reverse("gestion-ecarts")).json()
        self.assertEqual([ligne["ecart_total"] for ligne in bilan], [-160, 50])
        self.assertEqual(bilan[0]["nb_sessions_en_moins"], 1)

    # --- Annulation ---

    def test_serveur_ne_peut_pas_annuler(self):
        self.client.force_authenticate(self.karim)
        self.assertEqual(self.annuler().status_code, status.HTTP_403_FORBIDDEN)

    def test_gerant_annule_et_le_montant_attendu_baisse(self):
        self.client.force_authenticate(self.gerant)
        self.assertEqual(self.annuler().status_code, status.HTTP_200_OK)
        self.vente.refresh_from_db()
        self.assertTrue(self.vente.annulee)
        self.assertEqual(self.vente.annulee_par, self.gerant)
        self.assertEqual(self.session.calculer_montant_attendu(), 3000)

    def test_annulation_sans_motif_refusee(self):
        self.client.force_authenticate(self.gerant)
        self.assertEqual(self.annuler(motif="  ").status_code, status.HTTP_400_BAD_REQUEST)

    def test_double_annulation_refusee(self):
        self.client.force_authenticate(self.gerant)
        self.annuler()
        self.assertEqual(self.annuler().status_code, status.HTTP_400_BAD_REQUEST)

    def test_annulation_apres_cloture_refusee(self):
        cloturer_session(self.session, 3160)
        self.client.force_authenticate(self.gerant)
        self.assertEqual(self.annuler().status_code, status.HTTP_400_BAD_REQUEST)
# Create your tests here.
