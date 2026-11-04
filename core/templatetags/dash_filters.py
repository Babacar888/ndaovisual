"""Filtres de template personnalises pour les dashboards."""
from django import template
from ..models import Candidature

register = template.Library()


@register.filter
def filter_by_statut_en_cours(candidatures):
    return [c for c in candidatures if c.statut == Candidature.STATUT_EN_COURS]


@register.filter
def filter_by_statut_acceptee(candidatures):
    return [c for c in candidatures if c.statut == Candidature.STATUT_ACCEPTEE]


@register.filter
def filter_by_statut_refusee(candidatures):
    return [c for c in candidatures if c.statut == Candidature.STATUT_REFUSEE]


@register.filter
def filter_active(offres):
    return [o for o in offres if o.is_active()]