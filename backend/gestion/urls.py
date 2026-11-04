from django.urls import path

from . import views

urlpatterns = [
    path("sessions/", views.SessionsGestionView.as_view(), name="gestion-sessions"),
    path("ecarts/", views.EcartsParEmployeView.as_view(), name="gestion-ecarts"),
    path(
        "ventes/<int:pk>/annuler/",
        views.AnnulerVenteView.as_view(),
        name="gestion-annuler-vente",
    ),
]