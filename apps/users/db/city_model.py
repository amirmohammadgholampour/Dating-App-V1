from django.db import models
from django.utils.translation import gettext_lazy as _

class City(models.Model):
    """
    City (Shahrestan) model based on Iran's official divisions.
    Each city belongs to one province.
    """
    city_id = models.CharField(
        max_length=10,
        verbose_name=_("City ID")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("City name")
    )
    province = models.ForeignKey(
        'Province',
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name=_("Province")
    )
    
    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
        unique_together = ('city_id', 'province')
        ordering = ['province__name', 'name']
        indexes = [
            models.Index(fields=['province', 'name']),
            models.Index(fields=['city_id']),
        ]
    
    def __str__(self):
        return f"{self.name}, {self.province.name}"