from django.db import models 
from django.utils.translation import gettext_lazy as _ 

class Interest(models.Model): 
    name = models.CharField(
        max_length=255, 
        unique=True, 
        verbose_name=_("Interest name")
    )

    def __str__(self):
        return self.name 