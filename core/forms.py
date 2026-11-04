"""
Formulaires de l'application core.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Candidature, Entreprise, Offre, Utilisateur


class InscriptionForm(UserCreationForm):
    """Formulaire d'inscription avec selection du role."""

    role = forms.ChoiceField(
        choices=[
            (Utilisateur.ROLE_ETUDIANT, "Etudiant"),
            (Utilisateur.ROLE_ENTREPRISE, "Entreprise"),
        ],
        widget=forms.RadioSelect,
        label="Je m'inscris en tant que",
    )

    # Champs Etudiant
    formation = forms.CharField(max_length=200, required=False, label="Formation")
    competences = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Competences"
    )
    cv = forms.FileField(required=False, label="CV (PDF)")

    # Champs Entreprise
    nom_entreprise = forms.CharField(max_length=200, required=False, label="Nom de l'entreprise")
    secteur = forms.CharField(max_length=200, required=False, label="Secteur d'activite")
    adresse = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Adresse"
    )

    class Meta:
        model = Utilisateur
        fields = ("username", "email", "role", "first_name", "last_name")
        labels = {"username": "Nom d'utilisateur", "email": "Adresse e-mail"}

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        if role == Utilisateur.ROLE_ENTREPRISE and not cleaned_data.get("nom_entreprise"):
            self.add_error("nom_entreprise", "Le nom de l'entreprise est obligatoire.")
        elif role == Utilisateur.ROLE_ETUDIANT and not cleaned_data.get("formation"):
            self.add_error("formation", "La formation est obligatoire pour les etudiants.")
        return cleaned_data

    def save(self, commit=True):
        """Sauvegarde l'utilisateur puis cree le profil correspondant."""
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
            if user.role == Utilisateur.ROLE_ETUDIANT:
                Etudiant.objects.create(
                    utilisateur_ptr=user,
                    formation=self.cleaned_data.get("formation", ""),
                    competences=self.cleaned_data.get("competences", ""),
                    cv=self.cleaned_data.get("cv"),
                )
            elif user.role == Utilisateur.ROLE_ENTREPRISE:
                Entreprise.objects.create(
                    utilisateur_ptr=user,
                    nom_entreprise=self.cleaned_data.get("nom_entreprise", ""),
                    secteur=self.cleaned_data.get("secteur", ""),
                    adresse=self.cleaned_data.get("adresse", ""),
                )
        return user


class ConnexionForm(AuthenticationForm):
    """Formulaire de connexion personnalise."""
    username = forms.CharField(label="Nom d'utilisateur", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))


class OffreForm(forms.ModelForm):
    """Formulaire de creation / edition d'une offre."""

    class Meta:
        model = Offre
        fields = ["titre", "description", "type_offre", "localisation", "date_limite"]
        labels = {
            "titre": "Titre de l'offre",
            "description": "Description du poste",
            "type_offre": "Type d'offre",
            "localisation": "Localisation",
            "date_limite": "Date limite de candidature",
        }
        widgets = {
            "titre": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
            "type_offre": forms.Select(attrs={"class": "form-select"}),
            "localisation": forms.TextInput(attrs={"class": "form-control"}),
            "date_limite": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


class CandidatureForm(forms.ModelForm):
    """Formulaire de candidature a une offre."""

    class Meta:
        model = Candidature
        fields = ["lettre_motivation"]
        labels = {"lettre_motivation": "Lettre de motivation"}
        widgets = {
            "lettre_motivation": forms.Textarea(
                attrs={"rows": 6, "class": "form-control", "placeholder": "Expliquez pourquoi vous etes interesse..."}
            )
        }


class CandidatureStatutForm(forms.ModelForm):
    """Formulaire de changement de statut d'une candidature."""

    class Meta:
        model = Candidature
        fields = ["statut"]
        labels = {"statut": "Statut"}
        widgets = {"statut": forms.Select(attrs={"class": "form-select"})}


class OffreFiltreForm(forms.Form):
    """Formulaire de filtrage des offres publiques."""
    q = forms.CharField(required=False, label="Rechercher", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Mots-cles..."}))
    type_offre = forms.ChoiceField(
        choices=[("", "Tous les types")] + Offre.TYPE_CHOICES,
        required=False, label="Type", widget=forms.Select(attrs={"class": "form-select"}),
    )
    secteur = forms.ChoiceField(choices=[("", "Tous les secteurs")], required=False, label="Secteur", widget=forms.Select(attrs={"class": "form-select"}))
    localisation = forms.CharField(required=False, label="Localisation", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ville..."}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        secteurs = Entreprise.objects.exclude(secteur="").values_list("secteur", flat=True).distinct().order_by("secteur")
        self.fields["secteur"].choices = [("", "Tous les secteurs")] + [(s, s) for s in secteurs]