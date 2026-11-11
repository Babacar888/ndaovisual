"""URLs de l'application core."""
from django.urls import path
from . import views
from .views import EtudiantProfileUpdateView

app_name = "core"

urlpatterns = [
    # Authentification
    path("inscription/", views.InscriptionView.as_view(), name="register"),
    path("connexion/", views.ConnexionView.as_view(), name="login"),
    path("deconnexion/", views.DeconnexionView.as_view(), name="logout"),

    # Offres (publiques + CRUD)
    path("", views.OffreListView.as_view(), name="offre_list"),
    path("offres/<int:pk>/", views.OffreDetailView.as_view(), name="offre_detail"),
    path("offres/creer/", views.OffreCreateView.as_view(), name="offre_create"),
    path("offres/<int:pk>/modifier/", views.OffreUpdateView.as_view(), name="offre_update"),
    path("offres/<int:pk>/supprimer/", views.OffreDeleteView.as_view(), name="offre_delete"),

    # Candidature
    path("offres/<int:pk>/candidater/", views.CandidaterView.as_view(), name="candidater"),
    path("candidatures/<int:pk>/statut/", views.ChangerStatutCandidatureView.as_view(), name="changer_statut"),

    # Tableaux de bord
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
   path("dashboard/etudiant/", views.EtudiantDashboardView.as_view(), name="dashboard_etudiant"),
    path("dashboard/entreprise/", views.DashboardEntrepriseView.as_view(), name="dashboard_entreprise"),
    path("dashboard/admin/", views.DashboardAdminView.as_view(), name="dashboard_admin"),
    path('dashboard/etudiant/profil/', EtudiantProfileUpdateView.as_view(), name='etudiant_profil'),
]