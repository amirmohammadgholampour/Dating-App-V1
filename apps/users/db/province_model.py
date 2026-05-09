from django.db import models
from django.utils.translation import gettext_lazy as _


class Province(models.Model):
    """
    Province (Ostan) model based on Iran's official divisions.
    """
    province_id = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Province ID")
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Province name")
    )
    
    class Meta:
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")
        ordering = ['name']
    
    def __str__(self):
        return self.name