from django import forms
from django.contrib.auth.forms import UserChangeForm

from .models import PIN_LONGUEUR, Employe, valider_pin


class EmployeChangeForm(UserChangeForm):
    """Fiche d'un employé dans l'administration, avec un champ pour le PIN."""

    nouveau_pin = forms.CharField(
        label="Nouveau code PIN",
        required=False,
        max_length=PIN_LONGUEUR,
        widget=forms.PasswordInput(),
        help_text="Laissez vide pour garder le PIN actuel. "
        "Définir un nouveau PIN débloque aussi le compte.",
    )

    class Meta(UserChangeForm.Meta):
        model = Employe

    def clean_nouveau_pin(self):
        pin = self.cleaned_data["nouveau_pin"]
        if pin:
            valider_pin(pin)
        return pin

    def save(self, commit=True):
        employe = super().save(commit=False)
        pin = self.cleaned_data.get("nouveau_pin")
        if pin:
            employe.definir_pin(pin)
        if commit:
            employe.save()
        return employe