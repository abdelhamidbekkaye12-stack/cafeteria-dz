from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from .models import SessionCaisse, SortieCaisse, Vente
from .services import declarer_sortie, enregistrer_vente
from .models import SessionCaisse
from django.core.exceptions import ValidationError
from .services import cloturer_session, declarer_sortie, enregistrer_vente
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
        cloturer_session(premiere, 3000)

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
        cloturer_session(self.session, 3000)
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [(self.cafe.pk, 1)], montant_recu=100)

    def test_vente_vide_refusee(self):
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [], montant_recu=100)

    def test_quantite_nulle_refusee(self):
        with self.assertRaises(ValidationError):
            enregistrer_vente(self.session, [(self.cafe.pk, 0)], montant_recu=100)
# Create your tests here.
class MontantAttenduTests(TestCase):
    """Vérifie le calcul du montant qui devrait se trouver dans le tiroir."""

    def setUp(self):
        self.karim = Employe.objects.create_user(username="karim")
        self.gerant = Employe.objects.create_user(username="gerant", role="GERANT")
        self.session = SessionCaisse.objects.create(employe=self.karim, fond_initial=3000)
        boissons = Categorie.objects.create(nom="Boissons chaudes")
        self.cafe = Produit.objects.create(nom="Café express", categorie=boissons, prix=80)

    def test_sans_vente_le_montant_attendu_est_le_fond(self):
        self.assertEqual(self.session.calculer_montant_attendu(), 3000)

    def test_les_ventes_augmentent_le_montant_attendu(self):
        enregistrer_vente(self.session, [(self.cafe.pk, 2)], montant_recu=200)
        self.assertEqual(self.session.calculer_montant_attendu(), 3160)

    def test_les_sorties_diminuent_le_montant_attendu(self):
        declarer_sortie(self.session, 500, "Livreur de pain")
        self.assertEqual(self.session.calculer_montant_attendu(), 2500)

    def test_une_vente_annulee_ne_compte_pas(self):
        vente = enregistrer_vente(self.session, [(self.cafe.pk, 2)], montant_recu=200)
        vente.annulee = True
        vente.annulee_le = timezone.now()
        vente.annulee_par = self.gerant
        vente.motif_annulation = "Erreur de saisie"
        vente.save()
        self.assertEqual(self.session.calculer_montant_attendu(), 3000)


class DeclarerSortieTests(TestCase):
    """Vérifie les règles des sorties de caisse."""

    def setUp(self):
        karim = Employe.objects.create_user(username="karim")
        self.session = SessionCaisse.objects.create(employe=karim, fond_initial=3000)

    def test_sortie_normale_acceptee(self):
        sortie = declarer_sortie(self.session, 500, "  Livreur de pain  ")
        self.assertEqual(sortie.motif, "Livreur de pain")

    def test_motif_trop_court_refuse(self):
        with self.assertRaises(ValidationError):
            declarer_sortie(self.session, 500, "x")

    def test_motif_fait_d_espaces_refuse(self):
        with self.assertRaises(ValidationError):
            declarer_sortie(self.session, 500, "       ")

    def test_sortie_superieure_au_tiroir_refusee(self):
        with self.assertRaises(ValidationError):
            declarer_sortie(self.session, 5000, "Achat de lait")
        self.assertEqual(SortieCaisse.objects.count(), 0)

    def test_sortie_session_fermee_refusee(self):
        cloturer_session(self.session, 3000)
        with self.assertRaises(ValidationError):
            declarer_sortie(self.session, 500, "Livreur de pain")

class CloturerSessionTests(TestCase):
    """Vérifie la clôture de caisse et le calcul de l'écart."""

    def setUp(self):
        karim = Employe.objects.create_user(username="karim")
        self.session = SessionCaisse.objects.create(employe=karim, fond_initial=3000)
        boissons = Categorie.objects.create(nom="Boissons chaudes")
        self.cafe = Produit.objects.create(nom="Café express", categorie=boissons, prix=80)
        enregistrer_vente(self.session, [(self.cafe.pk, 25)], montant_recu=2000)
        declarer_sortie(self.session, 450, "Livreur de pain")
        # Montant attendu : 3000 + 2000 - 450 = 4550 DA

    def test_caisse_juste_ecart_nul(self):
        session = cloturer_session(self.session, 4550)
        self.assertEqual(session.montant_attendu, 4550)
        self.assertEqual(session.ecart, 0)

    def test_argent_manquant_ecart_negatif(self):
        session = cloturer_session(self.session, 4350)
        self.assertEqual(session.ecart, -200)

    def test_argent_en_trop_ecart_positif(self):
        session = cloturer_session(self.session, 4600)
        self.assertEqual(session.ecart, 50)

    def test_session_fermee_apres_cloture(self):
        session = cloturer_session(self.session, 4550)
        self.assertFalse(session.est_ouverte)

    def test_double_cloture_refusee(self):
        cloturer_session(self.session, 4550)
        with self.assertRaises(ValidationError):
            cloturer_session(self.session, 9999)

    def test_montant_negatif_refuse(self):
        with self.assertRaises(ValidationError):
            cloturer_session(self.session, -1)

    def test_ecart_falsifie_refuse_par_la_base(self):
        session = cloturer_session(self.session, 4350)
        session.ecart = 0
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                session.save()