# Plateforme de Gestion des Stages et Emplois

Projet Django 5 — Licence 3 POO Python Django

## Description

Plateforme web permettant aux etudiants de rechercher et postuler a des offres
de stages et d'emplois, et aux entreprises de publier des offres et de gerer
les candidatures recues.

## Principes POO appliques

- **Heritage** : `Etudiant` et `Entreprise` heritent de `Utilisateur` (AbstractUser)
- **Polymorphisme** : la methode `dashboard()` est redefinie dans chaque sous-classe
  (`Etudiant.dashboard()` retourne les candidatures, `Entreprise.dashboard()` retourne les offres)
- **Encapsulation** : utilisation de `@property` (`est_expiree`) et de methodes metier
  (`cloturer()`, `candidater()`, `changer_statut()`)
- **Abstraction** : `Utilisateur` sert de classe de base avec `get_dashboard_url()` polymorphe

## Modeles

| Modele        | Description                                  |
|---------------|----------------------------------------------|
| Utilisateur   | AbstractUser + role (etudiant/entreprise/admin) |
| Etudiant      | Herite de Utilisateur — formation, competences, cv |
| Entreprise    | Herite de Utilisateur — nom_entreprise, secteur, adresse |
| Offre         | Stage/emploi publie par une entreprise       |
| Candidature   | Lien unique etudiant ↔ offre (unique_together) |

## Installation

```bash
# 1. Installer les dependances
pip install -r requirements.txt

# 2. Creer la base de donnees (migrations)
python manage.py makemigrations core
python manage.py migrate

# 3. Creer un superutilisateur (admin)
python manage.py createsuperuser

# 4. Lancer le serveur de developpement
python manage.py runserver
```

Le site est accessible sur **http://127.0.0.1:8000/**

## Structure du projet

```
stage_platform/          # Configuration du projet Django
    settings.py
    urls.py
core/                    # Application principale
    models.py            # Modeles avec POO
    views.py             # Vues basees sur les classes (CBV)
    forms.py             # Formulaires
    admin.py             # Interface d'administration
    urls.py              # Routes
    templates/core/      # Templates Bootstrap 5
        base.html
        register.html
        login.html
        offre_list.html
        offre_detail.html
        offre_form.html
        offre_confirm_delete.html
        dashboard_etudiant.html
        dashboard_entreprise.html
        dashboard_admin.html
    templatetags/        # Filtres personnalises
requirements.txt
README.md
manage.py
```

## Fonctionnalites

### Authentification
- Inscription avec selection du role (etudiant ou entreprise)
- Connexion / Deconnexion
- Redirection automatique vers le dashboard correspondant au role

### Offres
- Liste publique des offres avec filtres (type, secteur, localisation, recherche)
- Detail d'une offre
- CRUD complet pour les entreprises (creer, modifier, supprimer)
- Cloture automatique a l'expiration de la date limite

### Candidatures
- Un etudiant peut candidater une seule fois par offre (unique_together)
- Tableau de bord etudiant: liste des candidatures avec statut
- Tableau de bord entreprise: candidatures recues + changement de statut
  (soumise -> en_cours -> acceptee / refusee)

### Administration
- Tableau de bord admin avec statistiques globales
- Interface d'administration Django native (/admin/)

## Decorateurs de protection par role

```python
@role_required(Utilisateur.ROLE_ENTREPRISE)
def ma_vue(request):
    ...

@etudiant_required
class MaVue(View):
    ...
```

## Technologies

- Python 3.11+
- Django 5.0
- Bootstrap 5.3
- SQLite (base de donnees par defaut)
- Bootstrap Icons
