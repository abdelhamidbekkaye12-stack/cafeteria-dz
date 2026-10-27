from django.contrib import admin

from .models import Categorie, Produit


class SansSuppressionMixin:
    """Interdit la suppression : on désactive au lieu de supprimer."""

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Categorie)
class CategorieAdmin(SansSuppressionMixin, admin.ModelAdmin):
    list_display = ["nom", "ordre", "active"]
    list_editable = ["ordre", "active"]
    search_fields = ["nom"]


@admin.register(Produit)
class ProduitAdmin(SansSuppressionMixin, admin.ModelAdmin):
    list_display = ["nom", "categorie", "prix", "en_vente", "modifie_le"]
    list_filter = ["categorie", "en_vente"]
    search_fields = ["nom"]
    readonly_fields = ["cree_le", "modifie_le"]