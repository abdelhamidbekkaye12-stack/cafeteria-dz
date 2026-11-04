from django.urls import path

from . import views

urlpatterns = [
    path("produits/", views.ProduitsEnVenteView.as_view(), name="produits-en-vente"),
]