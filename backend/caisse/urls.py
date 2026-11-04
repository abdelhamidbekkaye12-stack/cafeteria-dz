from django.urls import path

from . import views

urlpatterns = [
    path("session/", views.SessionCouranteView.as_view(), name="session-courante"),
    path("session/ouvrir/", views.OuvrirSessionView.as_view(), name="session-ouvrir"),
    path("session/cloturer/", views.CloturerSessionView.as_view(), name="session-cloturer"),
    path("ventes/", views.VenteView.as_view(), name="ventes"),
    path("sorties/", views.SortieView.as_view(), name="sorties"),
]