from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

PIN_LONGUEUR = 4
PIN_MAX_TENTATIVES = 5
PIN_INTERDITS = {"0000", "1111", "1234", "4321", "9999"}

def valider_pin(pin_brut):
    """Lève une ValidationError si le PIN ne respecte pas les règles."""
    if not (pin_brut.isascii() and pin_brut.isdigit()):
        raise ValidationError("Le PIN ne doit contenir que des chiffres.")
    if len(pin_brut) != PIN_LONGUEUR:
        raise ValidationError(f"Le PIN doit contenir {PIN_LONGUEUR} chiffres.")
    if pin_brut in PIN_INTERDITS:
        raise ValidationError("Ce PIN est trop facile à deviner.")
class Employe(AbstractUser):
    """Un employé de la cafétéria : gérant ou serveur."""

    class Role(models.TextChoices):
        GERANT = "GERANT", "Gérant"
        SERVEUR = "SERVEUR", "Serveur"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.SERVEUR,
    )
    telephone = models.CharField(max_length=20, blank=True)

    # --- Code PIN ---
    pin_hash = models.CharField(max_length=128, blank=True, editable=False)
    pin_tentatives = models.PositiveSmallIntegerField(default=0)
    pin_verrouille = models.BooleanField(default=False)

    class Meta:
        verbose_name = "employé"
        verbose_name_plural = "employés"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def definir_pin(self, pin_brut):
        """Vérifie le PIN, puis enregistre son empreinte (jamais le PIN lui-même)."""
        valider_pin(pin_brut)
        self.pin_hash = make_password(pin_brut)
        self.pin_tentatives = 0
        self.pin_verrouille = False
        
    def verifier_pin(self, pin_brut):
        """Renvoie True si le PIN est correct. Verrouille après trop d'erreurs."""
        if self.pin_verrouille or not self.pin_hash:
            return False

        if check_password(pin_brut, self.pin_hash):
            self.pin_tentatives = 0
            self.save(update_fields=["pin_tentatives"])
            return True

        self.pin_tentatives += 1
        if self.pin_tentatives >= PIN_MAX_TENTATIVES:
            self.pin_verrouille = True
        self.save(update_fields=["pin_tentatives", "pin_verrouille"])
        return False