from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/comptes/", include("comptes.urls")),
    path("api/catalogue/", include("catalogue.urls")),
    path("api/caisse/", include("caisse.urls")),
    path("api/gestion/", include("gestion.urls")),
]