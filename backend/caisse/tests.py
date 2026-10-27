from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import SessionCaisse

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

# Create your tests here.
