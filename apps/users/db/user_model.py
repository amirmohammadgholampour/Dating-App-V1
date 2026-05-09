from django.db import models 
from django.contrib.auth.models import (
    AbstractBaseUser, 
    BaseUserManager, 
    PermissionsMixin 
)
from django.utils import timezone 
from django.utils.translation import gettext_lazy as _ 
from django.core.exceptions import ValidationError
from apps.users.db.interest_model import Interest

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required.")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin): 
    class Gender(models.TextChoices): 
        MALE = "male" 
        FEMALE = "female" 
        OTHER = "other" 

    def validation_iran_phone_number(value): 
        if not isinstance(value, str): 
            raise ValidationError(
                _("Phone number must be a string."), 
                code="invalid_type" 
            )
        
        if len(value) != 11: 
            raise ValidationError(
                _("Phone number must be exactly 11 digits."), 
                params={"length": len(value)}, 
                code="invalid_length" 
            )
        
        if not value.isdigit(): 
            raise ValidationError(
                _("Phone number must contain only digits (0-9)."),
                code="invalid_chars"
            )
        
        if not value.startswith("09"): 
            raise ValidationError(
                _("Phone number must start with 09."),
                code='invalid_prefix'
            )

    phone_number = models.CharField(
        max_length=11,
        unique=True,
        verbose_name=_("Phone number"), 
        validators=[validation_iran_phone_number]
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    first_name = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("First name"))
    last_name = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Last name"))

    profile_picture = models.ImageField(
        upload_to="profile_pictures/", 
        verbose_name=_("Profile picture"), 
        null=True, 
        blank=True 
    )

    age = models.IntegerField(
        verbose_name=_("Age"), 
        null=True, 
        blank=True 
    )

    gender = models.CharField(
        max_length=255, 
        choices=Gender.choices, 
        verbose_name=_("Gender"), 
        default=Gender.MALE, 
        blank=True,
        null=True
    ) 

    province = models.ForeignKey(
        "Province",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_("Province")
    )
    city = models.ForeignKey(
        "City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_("City (Shahrestan)")
    )

    bio = models.TextField(
        max_length=500, 
        verbose_name=_("Biography"), 
        blank=True, 
        null=True
    )

    interests = models.ManyToManyField(
        Interest,
        through="UserInterest",
        verbose_name=_('Interests'), 
        blank=True
    ) 

    def __str__(self):
        f_name = self.first_name 
        l_name = self.last_name 
        if f_name or l_name: 
            return f"{f_name} {l_name}".strip() 
        return self.phone_number
    
class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True) 