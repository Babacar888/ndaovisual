import os
import sys
import django

# Dit à Python : le projet est dans le dossier parent de core/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stage_platform.settings')
django.setup()

from datetime import date, timedelta
from core.models import Offre, Entreprise

entreprise = Entreprise.objects.first()
if not entreprise:
    print("Crée d'abord une entreprise !")
else:
    offres = [
        ("Stage Développeur Web Django", "stage", "Dakar, Plateau", "Développe des applications web avec Django. Tu travailleras sur de vrais projets."),
        ("Stage Assistant Comptable", "stage", "Dakar, Almadies", "Aide à la comptabilité, saisie, Excel et suivi des factures."),
        ("Développeur Frontend React Junior", "emploi", "Dakar, Mermoz", "Développement d'interfaces avec React et JavaScript."),
        ("Stage Marketing Digital", "stage", "Rufisque", "Gestion des réseaux sociaux, création de contenu avec Canva."),
        ("Stage Data Analyst", "stage", "Dakar, Diamniadio", "Analyse de données avec Python, Excel et SQL."),
        ("Commercial Terrain", "emploi", "Thiès", "Prospection et vente sur le terrain."),
        ("Stage Graphiste / Designer UI", "stage", "Dakar, Parcelles", "Création de maquettes avec Figma et Photoshop."),
        ("Technicien Support Informatique", "emploi", "Dakar, Pikine", "Maintenance, dépannage et support réseaux."),
    ]

    for titre, type_offre, localisation, description in offres:
        Offre.objects.get_or_create(
            titre=titre,
            entreprise=entreprise,
            defaults={
                'type_offre': type_offre,
                'localisation': localisation,
                'description': description,
                'date_limite': date.today() + timedelta(days=30),
                'statut': 'ouverte',
            }
        )
    print("8 offres créées !")