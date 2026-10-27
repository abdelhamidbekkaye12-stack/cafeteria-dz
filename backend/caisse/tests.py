from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import SessionCaisse
from django.core.exceptions import ValidationError

from catalogue.models import Categorie, Produit

from .models import Vente
from .services import enregistrer_vente
Employe = get_user_model()


class SessionCaisseTests(TestCase):
    """Vérifie les règles d'ouverture des sessions de caisse."""

    def setUp(self):
        self.karim = Employe.objects.create_user(username="karim")

    def test_nouvelle_session_est_ouverte(self):
        session = SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)
        self.assertTrue(session.est_ouverte)

    def test_deux_sessions_ouvertes_interdites(self):
        SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)

    def test_nouvelle_session_possible_apres_cloture(self):
        premiere = SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)
        premiere.fermee_le = timezone.now()
        premiere.save()

        seconde = SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)
        self.assertTrue(seconde.est_ouverte)

    def test_deux_employes_ont_chacun_leur_session(self):
        amine = Employe.objects.create_user(username="amine")
        SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)
        SessionCaisse.objects.create(employe=amine, fond_initial=2000)

        ouvertes = SessionCaisse.objects.filter(fermee_le__isnull=True)
        self.assertEqual(ouvertes.count(), 2)
class EnregistrerVenteTests(TestCase):
    """Vérifie le service d'encaissement."""

    def setUp(self):
        karim = Employe.objects.create_user(username="karim")
        self.session = SessionCaisse.objects.create(employe=karim, fond_initial=3000)
        boissons = Categorie.objects.create(nom="Boissons chaudes")
        galettes = Categorie.objects.create(nom="Galettes")
        self.cafe = Produit.objects.create(nom="Café express", categorie=boissons, prix=80)
        self.msemen = Produit.objects.create(nom="Msemen", categorie=galettes, prix=50)

    # --- Le cas normal ---

    def test_vente_calcule_le_total_et_le_rendu(self):
        vente = enregistrer_vente(
            self.session, [(self.cafe.pk, 2), (self.msemen.pk, 1)], montant_recu=500
        )
        self.assertEqual(vente.total, 210)
        self.assertEqual(vente.rendu, 290)
        self.assertEqual(vente.lignes.count(), 2)

    def test_total_egal_somme_des_lignes(self):
        vente = enregistrer_vente(
            self.session, [(self.cafe.pk, 3), (self.msemen.pk, 2)], montant_recu=1000
        )
        somme = sum(ligne.sous_total for ligne in vente.lignes.all())
        self.assertEqual(vente.total, somme)

    def test_vente_signee_par_le_serveur_de_la_session(self):
        vente = enregistrer_vente(self.session, [(self.cafe.pk, 1)], montant_recu=80)
        self.assertEqual(vente.employe.username, "karim")

    def test_changement_de_prix_ne_modifie_pas_le_passe(self):
        vente = enregistrer_vente(self.session, [(self.cafe.pk, 1)], montant_recu=100)
        self.cafe.prix = 100
        self.cafe.save()
        ligne = vente.lignes.get()
        self.assertEqual(ligne.prix_unitaire, 80)

    # --- Les refus ---

    def test_montant_insuffisant_refuse_et_rien_enregistre(self):
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [(self.cafe.pk, 2)], montant_recu=100)
        self.assertEqual(Vente.objects.count(), 0)

    def test_produit_retire_de_la_vente_refuse(self):
        self.cafe.en_vente = False
        self.cafe.save()
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [(self.cafe.pk, 1)], montant_recu=100)

    def test_session_fermee_refusee(self):
        self.session.fermee_le = timezone.now()
        self.session.save()
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [(self.cafe.pk, 1)], montant_recu=100)

    def test_vente_vide_refusee(self):
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [], montant_recu=100)

    def test_quantite_nulle_refusee(self):
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [(self.cafe.pk, 0)], montant_recu=100)
# Create your tests here.
