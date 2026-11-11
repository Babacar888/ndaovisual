"""
Modeles de l'application core.

Application des principes POO:
  - Heritage: Etudiant et Entreprise heritent de Utilisateur (multi-table)
  - Polymorphisme: methode dashboard() redefinie dans chaque sous-classe
  - Encapsulation: utilisation de @property (est_expiree) et methodes metier
  - Abstraction: AbstractUser comme classe de base
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Utilisateur(AbstractUser):
    """Utilisateur de base avec un role (etudiant / entreprise / admin).

    Herite d'AbstractUser (heritage multi-table Django) et ajoute
    la notion de role pour le polymorphisme des tableaux de bord.
    """

    ROLE_ETUDIANT = "etudiant"
    ROLE_ENTREPRISE = "entreprise"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_ETUDIANT, "Etudiant"),
        (ROLE_ENTREPRISE, "Entreprise"),
        (ROLE_ADMIN, "Administrateur"),
    ]

    email = models.EmailField("Adresse e-mail", unique=True)
    role = models.CharField(
        "Role", max_length=20, choices=ROLE_CHOICES, default=ROLE_ETUDIANT
    )
    date_inscription = models.DateTimeField("Date d'inscription", auto_now_add=True)

    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-date_inscription"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # --- Polymorphisme --------------------------------------------------
    def get_dashboard_url(self):
        """Retourne l'URL du tableau de bord selon le role."""
        if self.role == self.ROLE_ETUDIANT:
            return reverse("core:dashboard_etudiant")
        if self.role == self.ROLE_ENTREPRISE:
            return reverse("core:dashboard_entreprise")
        if self.role == self.ROLE_ADMIN:
            return reverse("core:dashboard_admin")
        return reverse("core:offre_list")

    def dashboard(self):
        """Methode polymorphe: retourne les donnees du tableau de bord.

        Redefinie dans Etudiant et Entreprise. Par defaut: vide.
        """
        return {}

    def as_etudiant(self):
           try:
            return self.etudiant
           except Etudiant.DoesNotExist:
            e = Etudiant(utilisateur_ptr=self)
            e.save_base(raw=True)
            return Etudiant.objects.get(pk=self.pk)

    def as_entreprise(self):
        try:
            return self.entreprise
        except Entreprise.DoesNotExist:
            e = Entreprise(utilisateur_ptr=self)
            e.save_base(raw=True)
            return Entreprise.objects.get(pk=self.pk)


class Etudiant(Utilisateur):
    """Etudiant: herite de Utilisateur (heritage multi-table).

    Encapsule les informations specifiques a un etudiant chercheur de stage/emploi.
    """

    formation = models.CharField("Formation", max_length=200, blank=True)
    competences = models.TextField("Competences", blank=True)
    cv = models.FileField("CV (PDF)", upload_to="cv/", null=True, blank=True)

    class Meta:
        verbose_name = "Etudiant"
        verbose_name_plural = "Etudiants"

    def __str__(self):
        return f"Etudiant: {self.username}"

    # --- Polymorphisme --------------------------------------------------
    def dashboard(self):
        """Retourne les candidatures de l'etudiant (polymorphisme)."""
        return self.candidatures.select_related("offre", "offre__entreprise").all()

    # --- Methode metier -------------------------------------------------
    def candidater(self, offre, lettre_motivation=""):
        """Candidater a une offre. Cree une candidature si inexistante.

        Garantit qu'un etudiant ne candidaten pas deux fois a la meme offre
        (unique_together dans Candidature).
        """
        candidature, creee = Candidature.objects.get_or_create(
            etudiant=self,
            offre=offre,
            defaults={"lettre_motivation": lettre_motivation},
        )
        return candidature, creee


class Entreprise(Utilisateur):
    """Entreprise: herite de Utilisateur (heritage multi-table).

    Encapsule les informations specifiques a une entreprise qui publie des offres.
    """

    nom_entreprise = models.CharField("Nom de l'entreprise", max_length=200, blank=True)
    secteur = models.CharField("Secteur d'activite", max_length=200, blank=True)
    adresse = models.TextField("Adresse", blank=True)

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"

    def __str__(self):
        return f"Entreprise: {self.nom_entreprise or self.username}"

    # --- Polymorphisme --------------------------------------------------
    def dashboard(self):
        """Retourne les offres publiees par l'entreprise (polymorphisme)."""
        return self.offres.prefetch_related("candidatures").all()

    # --- Methode metier -------------------------------------------------
    def publier_offre(self, **kwargs):
        """Publie une nouvelle offre pour cette entreprise."""
        return Offre.objects.create(entreprise=self, **kwargs)


class Offre(models.Model):
    """Offre de stage ou d'emploi publiee par une entreprise."""

    TYPE_STAGE = "stage"
    TYPE_EMPLOI = "emploi"
    TYPE_CHOICES = [
        (TYPE_STAGE, "Stage"),
        (TYPE_EMPLOI, "Emploi"),
    ]

    STATUT_OUVERTE = "ouverte"
    STATUT_CLOTUREE = "cloturee"
    STATUT_CHOICES = [
        (STATUT_OUVERTE, "Ouverte"),
        (STATUT_CLOTUREE, "Cloturee"),
    ]

    titre = models.CharField("Titre", max_length=200)
    description = models.TextField("Description")
    type_offre = models.CharField("Type", max_length=10, choices=TYPE_CHOICES)
    localisation = models.CharField("Localisation", max_length=200, blank=True)
    date_limite = models.DateField("Date limite de candidature", null=True, blank=True)
    statut = models.CharField(
        "Statut", max_length=10, choices=STATUT_CHOICES, default=STATUT_OUVERTE
    )
    entreprise = models.ForeignKey(
        Entreprise, verbose_name="Entreprise", on_delete=models.CASCADE, related_name="offres"
    )
    date_publication = models.DateTimeField("Date de publication", auto_now_add=True)

    class Meta:
        verbose_name = "Offre"
        verbose_name_plural = "Offres"
        ordering = ["-date_publication"]

    def __str__(self):
        return f"{self.titre} - {self.entreprise.nom_entreprise or self.entreprise.username}"

    # --- Encapsulation via @property ------------------------------------
    @property
    def est_expiree(self):
        """Retourne True si la date limite est depassee (encapsulation)."""
        if self.date_limite is None:
            return False
        return timezone.now().date() > self.date_limite

    # --- Methodes metier ------------------------------------------------
    def is_active(self):
        """Une offre est active si elle est ouverte et non expiree."""
        return self.statut == self.STATUT_OUVERTE and not self.est_expiree

    def cloturer(self):
        """Cloture l'offre: change le statut et sauvegarde."""
        self.statut = self.STATUT_CLOTUREE
        self.save(update_fields=["statut"])

    def nombre_candidatures(self):
        return self.candidatures.count()


class Candidature(models.Model):
    """Candidature d'un etudiant a une offre."""

    STATUT_SOUMISE = "soumise"
    STATUT_EN_COURS = "en_cours"
    STATUT_ACCEPTEE = "acceptee"
    STATUT_REFUSEE = "refusee"
    STATUT_CHOICES = [
        (STATUT_SOUMISE, "Soumise"),
        (STATUT_EN_COURS, "En cours de traitement"),
        (STATUT_ACCEPTEE, "Acceptee"),
        (STATUT_REFUSEE, "Refusee"),
    ]

    etudiant = models.ForeignKey(
        Etudiant, verbose_name="Etudiant", on_delete=models.CASCADE, related_name="candidatures"
    )
    offre = models.ForeignKey(
        Offre, verbose_name="Offre", on_delete=models.CASCADE, related_name="candidatures"
    )
    date_candidature = models.DateTimeField("Date de candidature", auto_now_add=True)
    statut = models.CharField(
        "Statut", max_length=20, choices=STATUT_CHOICES, default=STATUT_SOUMISE
    )
    lettre_motivation = models.TextField("Lettre de motivation", blank=True)

    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        unique_together = ("etudiant", "offre")
        ordering = ["-date_candidature"]

    def __str__(self):
        return f"{self.etudiant.username} -> {self.offre.titre} ({self.get_statut_display()})"

    # --- Methode metier -------------------------------------------------
    def changer_statut(self, nouveau_statut):
        """Change le statut de la candidature et sauvegarde."""
        if nouveau_statut in dict(self.STATUT_CHOICES):
            self.statut = nouveau_statut
            self.save(update_fields=["statut"])
            return True
        return False