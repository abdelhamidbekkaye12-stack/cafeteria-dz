from django.urls import path

from . import views

urlpatterns = [
    path("employes/", views.EmployesConnexionView.as_view(), name="employes-connexion"),
    path("connexion/", views.ConnexionPinView.as_view(), name="connexion-pin"),
]