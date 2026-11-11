"""
Vues de l'application core.

Utilisation des vues basees sur les classes (CBV) et de decorateurs
de protection par role.

Principes:
  - CBV (Class-Based Views) pour le CRUD des offres
  - Decorateurs de protection par role
  - Polymorphisme: chaque utilisateur est redirige vers son dashboard
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from .forms import (
    CandidatureForm, CandidatureStatutForm, ConnexionForm,
    InscriptionForm, OffreFiltreForm, OffreForm, EtudiantProfilForm,
)
from .models import Candidature, Entreprise, Etudiant, Offre, Utilisateur


# =========================================================================
#  DECORATEURS DE PROTECTION PAR ROLE
# =========================================================================

def role_required(*roles):
    """Decorateur: autorise l'acces uniquement aux roles specifies."""
    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "Vous n'avez pas l'autorisation d'acceder a cette page.")
                return HttpResponseRedirect(request.user.get_dashboard_url())
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def etudiant_required(view_func):
    return role_required(Utilisateur.ROLE_ETUDIANT)(view_func)


def entreprise_required(view_func):
    return role_required(Utilisateur.ROLE_ENTREPRISE)(view_func)


def admin_required(view_func):
    return role_required(Utilisateur.ROLE_ADMIN)(view_func)


# =========================================================================
#  VUES D'AUTHENTIFICATION
# =========================================================================

class InscriptionView(CreateView):
    """Inscription d'un nouvel utilisateur avec selection du role (CBV)."""
    form_class = InscriptionForm
    template_name = "core/register.html"
    success_url = reverse_lazy("core:login")

    def form_valid(self, form):
        messages.success(self.request, "Votre compte a ete cree. Vous pouvez vous connecter.")
        return super().form_valid(form)


class ConnexionView(LoginView):
    """Connexion utilisateur (CBV)."""
    template_name = "core/login.html"
    authentication_form = ConnexionForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.request.user.get_dashboard_url()


class DeconnexionView(LogoutView):
    """Deconnexion utilisateur (CBV)."""
    next_page = reverse_lazy("core:offre_list")
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# =========================================================================
#  VUES DES OFFRES (CRUD + filtrage public)
# =========================================================================

class OffreListView(ListView):
    """Liste publique des offres avec filtres (CBV)."""
    model = Offre
    template_name = "core/offre_list.html"
    context_object_name = "offres"
    paginate_by = 6

    def get_queryset(self):
        queryset = Offre.objects.select_related("entreprise").all()
        self.filtre_form = OffreFiltreForm(self.request.GET)
        if self.filtre_form.is_valid():
            data = self.filtre_form.cleaned_data
            q = data.get("q", "").strip()
            if q:
                queryset = queryset.filter(Q(titre__icontains=q) | Q(description__icontains=q))
            type_offre = data.get("type_offre")
            if type_offre:
                queryset = queryset.filter(type_offre=type_offre)
            secteur = data.get("secteur")
            if secteur:
                queryset = queryset.filter(entreprise__secteur=secteur)
            localisation = data.get("localisation", "").strip()
            if localisation:
                queryset = queryset.filter(localisation__icontains=localisation)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtre_form"] = self.filtre_form
        return context


class OffreDetailView(DetailView):
    """Detail d'une offre (CBV)."""
    model = Offre
    template_name = "core/offre_detail.html"
    context_object_name = "offre"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and self.request.user.role == Utilisateur.ROLE_ETUDIANT:
            try:
                etudiant = self.request.user.as_etudiant()
                context["deja_candidate"] = Candidature.objects.filter(
                    etudiant=etudiant, offre=self.object
                ).exists()
            except Etudiant.DoesNotExist:
                context["deja_candidate"] = False
            context["candidature_form"] = CandidatureForm()
        else:
            context["deja_candidate"] = False
        return context


@method_decorator(entreprise_required, name="dispatch")
class OffreCreateView(LoginRequiredMixin, CreateView):
    """Creation d'une offre par une entreprise (CBV)."""
    model = Offre
    form_class = OffreForm
    template_name = "core/offre_form.html"
    success_url = reverse_lazy("core:dashboard_entreprise")

    def form_valid(self, form):
        form.instance.entreprise = self.request.user.as_entreprise()
        messages.success(self.request, "Votre offre a ete publiee avec succes.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titre_page"] = "Publier une offre"
        context["bouton_texte"] = "Publier"
        return context


@method_decorator(entreprise_required, name="dispatch")
class OffreUpdateView(LoginRequiredMixin, UpdateView):
    """Modification d'une offre par son entreprise (CBV)."""
    model = Offre
    form_class = OffreForm
    template_name = "core/offre_form.html"

    def get_queryset(self):
        return Offre.objects.filter(entreprise=self.request.user.as_entreprise())

    def get_success_url(self):
        messages.success(self.request, "L'offre a ete modifiee avec succes.")
        return reverse("core:offre_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titre_page"] = "Modifier l'offre"
        context["bouton_texte"] = "Enregistrer"
        return context


@method_decorator(entreprise_required, name="dispatch")
class OffreDeleteView(LoginRequiredMixin, DeleteView):
    """Suppression d'une offre par son entreprise (CBV)."""
    model = Offre
    template_name = "core/offre_confirm_delete.html"
    success_url = reverse_lazy("core:dashboard_entreprise")

    def get_queryset(self):
        return Offre.objects.filter(entreprise=self.request.user.as_entreprise())

    def form_valid(self, form):
        messages.success(self.request, "L'offre a ete supprimee.")
        return super().form_valid(form)


# =========================================================================
#  VUE DE CANDIDATURE (Etudiant)
# =========================================================================

@method_decorator(etudiant_required, name="dispatch")
class CandidaterView(LoginRequiredMixin, View):
    """Permet a un etudiant de candidater a une offre (une seule fois)."""

    def post(self, request, pk):
        offre = get_object_or_404(Offre, pk=pk)
        if not offre.is_active():
            messages.error(request, "Cette offre n'est plus accessible.")
            return redirect("core:offre_detail", pk=pk)
        etudiant = request.user.as_etudiant()
        form = CandidatureForm(request.POST)
        if form.is_valid():
            candidature, creee = etudiant.candidater(
                offre, lettre_motivation=form.cleaned_data["lettre_motivation"]
            )
            if creee:
                messages.success(request, "Votre candidature a ete soumise avec succes.")
            else:
                messages.warning(request, "Vous avez deja candidate a cette offre.")
            return redirect("core:dashboard_etudiant")
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
        return redirect("core:offre_detail", pk=pk)


# =========================================================================
#  TABLEAUX DE BORD (Dashboards)
# =========================================================================

@login_required
def dashboard_redirect(request):
    """Redirige vers le dashboard selon le role (polymorphisme)."""
    return redirect(request.user.get_dashboard_url())


@method_decorator(etudiant_required, name='dispatch')
class EtudiantDashboardView(LoginRequiredMixin, TemplateView):
  template_name = "core/dashboard_etudiant.html"
  def get_etudiant(self):
                # Si la ligne Etudiant n'existe pas, on crée juste la ligne enfant
                # en réutilisant le même id que l'Utilisateur, on ne recrée pas un user
                try:
                    return self.request.user.as_etudiant()
                except Etudiant.DoesNotExist:
                    etudiant = Etudiant(utilisateur_ptr=self.request.user)
                    etudiant.save_base(raw=True)
                    # On recharge pour être sûr
                    return Etudiant.objects.get(pk=self.request.user.pk)

  def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                etudiant = self.get_etudiant()
                context['etudiant'] = etudiant
                context['candidatures'] = Candidature.objects.filter(etudiant=etudiant)
                return context


@method_decorator(entreprise_required, name="dispatch")
class DashboardEntrepriseView(LoginRequiredMixin, TemplateView):
    """Tableau de bord de l'entreprise: ses offres + candidatures recues (CBV)."""
    template_name = "core/dashboard_entreprise.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.as_entreprise()
        context["offres"] = entreprise.dashboard()
        context["toutes_candidatures"] = (
            Candidature.objects.filter(offre__entreprise=entreprise)
            .select_related("etudiant", "offre")
            .order_by("-date_candidature")
        )
        context["entreprise"] = entreprise
        return context


@method_decorator(entreprise_required, name="dispatch")
class ChangerStatutCandidatureView(LoginRequiredMixin, View):
    """Permet a une entreprise de changer le statut d'une candidature."""

    def post(self, request, pk):
        candidature = get_object_or_404(
            Candidature, pk=pk, offre__entreprise=request.user.as_entreprise()
        )
        form = CandidatureStatutForm(request.POST, instance=candidature)
        if form.is_valid():
            candidature.changer_statut(form.cleaned_data["statut"])
            messages.success(request, "Le statut de la candidature a ete mis a jour.")
        else:
            messages.error(request, "Erreur lors de la mise a jour du statut.")
        return redirect("core:dashboard_entreprise")


@method_decorator(admin_required, name="dispatch")
class DashboardAdminView(LoginRequiredMixin, TemplateView):
    """Tableau de bord admin: statistiques globales (CBV)."""
    template_name = "core/dashboard_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_utilisateurs"] = Utilisateur.objects.count()
        context["total_etudiants"] = Etudiant.objects.count()
        context["total_entreprises"] = Entreprise.objects.count()
        context["total_offres"] = Offre.objects.count()
        context["offres_ouvertes"] = Offre.objects.filter(statut=Offre.STATUT_OUVERTE).count()
        context["total_candidatures"] = Candidature.objects.count()
        context["statuts_candidatures"] = Candidature.objects.values("statut").annotate(total=Count("id"))
        context["types_offres"] = Offre.objects.values("type_offre").annotate(total=Count("id"))
        context["dernieres_offres"] = Offre.objects.select_related("entreprise").order_by("-date_publication")[:5]
        context["dernieres_candidatures"] = Candidature.objects.select_related("etudiant", "offre").order_by("-date_candidature")[:5]
        return context
   
class EtudiantProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Etudiant
    form_class = EtudiantProfilForm
    template_name = "core/etudiant_profil.html"
    success_url = reverse_lazy('core:dashboard_etudiant')

    def get_object(self):
        return self.request.user.as_etudiant()