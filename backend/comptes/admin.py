from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Employe
from .forms import EmployeChangeForm

@admin.register(Employe)
class EmployeAdmin(UserAdmin):
    """Page de gestion des employés dans l'administration."""

    # La liste des employés
    list_display = ["username", "first_name", "last_name", "role", "is_active", "pin_verrouille"]
    list_filter = ["role", "is_active", "pin_verrouille"]
    search_fields = ["username", "first_name", "last_name", "telephone"]
    form = EmployeChangeForm
    # La fiche d'un employé existant
    fieldsets = UserAdmin.fieldsets + (
        ("Cafétéria", {"fields": ("role", "telephone")}),
          ("Code PIN", {"fields": ("nouveau_pin", "pin_tentatives", "pin_verrouille")}),
    )
    readonly_fields = ["pin_tentatives", "pin_verrouille"]

    # Le formulaire de création d'un employé
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Cafétéria", {"fields": ("first_name", "last_name", "role", "telephone")}),
    )
