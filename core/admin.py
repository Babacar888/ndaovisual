"""
Configuration de l'interface d'administration Django.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Candidature, Entreprise, Etudiant, Offre, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active", "date_inscription")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_inscription",)
    fieldsets = UserAdmin.fieldsets + (
        ("Infos supplementaires", {"fields": ("role", "date_inscription")}),
    )


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "formation", "has_cv")
    search_fields = ("username", "email", "formation")
    list_filter = ("formation",)

    def has_cv(self, obj):
        return bool(obj.cv)
    has_cv.boolean = True
    has_cv.short_description = "CV"


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "nom_entreprise", "secteur")
    search_fields = ("username", "email", "nom_entreprise", "secteur")
    list_filter = ("secteur",)


@admin.register(Offre)
class OffreAdmin(admin.ModelAdmin):
    list_display = ("titre", "type_offre", "entreprise", "localisation", "statut", "date_limite", "date_publication")
    list_filter = ("type_offre", "statut", "date_publication")
    search_fields = ("titre", "description", "localisation")
    date_hierarchy = "date_publication"
    raw_id_fields = ("entreprise",)


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "offre", "statut", "date_candidature")
    list_filter = ("statut", "date_candidature")
    search_fields = ("etudiant__username", "offre__titre")
    date_hierarchy = "date_candidature"
    raw_id_fields = ("etudiant", "offre")