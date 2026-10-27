from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import PIN_MAX_TENTATIVES, Employe


class PinTests(TestCase):
    """Vérifie le fonctionnement du code PIN des employés."""

    def setUp(self):
        self.karim = Employe.objects.create_user(username="karim")
        self.karim.definir_pin("4821")
        self.karim.save()

    # --- Stockage ---

    def test_pin_jamais_stocke_en_clair(self):
        self.assertNotIn("4821", self.karim.pin_hash)

    # --- Règles de validation ---

    def test_pin_trop_simple_refuse(self):
        with self.assertRaises(ValidationError):
            self.karim.definir_pin("1234")

    def test_pin_mauvaise_longueur_refuse(self):
        with self.assertRaises(ValidationError):
            self.karim.definir_pin("48")

    def test_pin_avec_lettres_refuse(self):
        with self.assertRaises(ValidationError):
            self.karim.definir_pin("48a1")

    def test_pin_chiffres_arabes_orientaux_refuse(self):
        with self.assertRaises(ValidationError):
            self.karim.definir_pin("٤٨٢١")

    # --- Vérification ---

    def test_bon_pin_accepte(self):
        self.assertTrue(self.karim.verifier_pin("4821"))

    def test_mauvais_pin_refuse(self):
        self.assertFalse(self.karim.verifier_pin("0000"))

    def test_succes_remet_le_compteur_a_zero(self):
        self.karim.verifier_pin("0000")
        self.karim.verifier_pin("4821")
        self.karim.refresh_from_db()
        self.assertEqual(self.karim.pin_tentatives, 0)

    # --- Verrouillage anti-vol ---

    def test_verrouillage_apres_trop_d_erreurs(self):
        for _ in range(PIN_MAX_TENTATIVES):
            self.karim.verifier_pin("0000")
        self.karim.refresh_from_db()
        self.assertTrue(self.karim.pin_verrouille)

    def test_bon_pin_refuse_si_verrouille(self):
        for _ in range(PIN_MAX_TENTATIVES):
            self.karim.verifier_pin("0000")
        self.assertFalse(self.karim.verifier_pin("4821"))

    def test_nouveau_pin_debloque_le_compte(self):
        for _ in range(PIN_MAX_TENTATIVES):
            self.karim.verifier_pin("0000")
        self.karim.definir_pin("7395")
        self.karim.save()
        self.assertTrue(self.karim.verifier_pin("7395"))
