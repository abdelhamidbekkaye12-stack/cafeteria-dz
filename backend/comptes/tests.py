from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
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
class ConnexionApiTests(APITestCase):
    """Vérifie le guichet /api/comptes/connexion/."""

    def setUp(self):
        self.url = reverse("connexion-pin")
        self.karim = Employe.objects.create_user(
            username="karim", first_name="Karim", last_name="Benali"
        )
        self.karim.definir_pin("4821")
        self.karim.save()

    def connecter(self, employe_id, pin):
        return self.client.post(self.url, {"employe_id": employe_id, "pin": pin}, format="json")

    # --- Le cas normal ---

    def test_bon_pin_renvoie_un_jeton(self):
        reponse = self.connecter(self.karim.pk, "4821")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        jeton = Token.objects.get(user=self.karim)
        self.assertEqual(reponse.json()["token"], jeton.key)

    def test_le_jeton_ouvre_l_api(self):
        jeton = self.connecter(self.karim.pk, "4821").json()["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {jeton}")
        reponse = self.client.get(reverse("produits-en-vente"))
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)

    # --- Les refus ---

    def test_mauvais_pin_refuse_sans_jeton(self):
        reponse = self.connecter(self.karim.pk, "9876")
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", reponse.json())

    def test_employe_inconnu_meme_reponse_que_mauvais_pin(self):
        mauvais_pin = self.connecter(self.karim.pk, "9876")
        inconnu = self.connecter(9999, "9876")
        self.assertEqual(mauvais_pin.status_code, inconnu.status_code)
        self.assertEqual(mauvais_pin.json(), inconnu.json())

    def test_employe_desactive_refuse(self):
        self.karim.is_active = False
        self.karim.save()
        reponse = self.connecter(self.karim.pk, "4821")
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compte_verrouille_apres_trop_d_erreurs(self):
        for _ in range(PIN_MAX_TENTATIVES):
            self.connecter(self.karim.pk, "9876")
        reponse = self.connecter(self.karim.pk, "4821")
        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

    def test_demande_mal_formee_refusee(self):
        reponse = self.client.post(self.url, {"pin": "4821"}, format="json")
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)


class EmployesConnexionApiTests(APITestCase):
    """Vérifie le guichet /api/comptes/employes/."""

    def setUp(self):
        self.url = reverse("employes-connexion")
        self.karim = Employe.objects.create_user(username="karim", first_name="Karim")
        self.karim.definir_pin("4821")
        self.karim.save()

    def noms_affiches(self):
        return [employe["nom"] for employe in self.client.get(self.url).json()]

    def test_accessible_sans_connexion(self):
        reponse = self.client.get(self.url)
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)

    def test_seuls_l_id_et_le_nom_sont_envoyes(self):
        employe = self.client.get(self.url).json()[0]
        self.assertEqual(set(employe.keys()), {"id", "nom"})

    def test_employe_sans_pin_absent(self):
        Employe.objects.create_user(username="comptable")
        self.assertEqual(self.noms_affiches(), ["Karim"])

    def test_employe_desactive_absent(self):
        self.karim.is_active = False
        self.karim.save()
        self.assertEqual(self.noms_affiches(), [])