from django.db import models 
from django.contrib.auth.models import (
    AbstractBaseUser, 
    BaseUserManager, 
    PermissionsMixin 
)
from django.utils import timezone 
from django.utils.translation import gettext_lazy as _ 
from django.core.exceptions import ValidationError
from datetime import date
from apps.users.db.interest_model import Interest

class UserManager(BaseUserManager):
    def create_user(self, phone_number=None, password=None, **extra_fields):
        email = extra_fields.get("email")
        if not phone_number and not email:
            raise ValueError("An email address or phone number is required.")
        if email:
            extra_fields["email"] = self.normalize_email(email).lower()
        user = self.model(phone_number=phone_number or None, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if not extra_fields.get('is_staff') or not extra_fields.get('is_superuser'):
            raise ValueError("Superusers must have is_staff=True and is_superuser=True.")
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
        null=True,
        blank=True,
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
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name=_("Email address"))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Date of birth"))

    profile_picture = models.ImageField(
        upload_to="profile_pictures/", 
        verbose_name=_("Profile picture"), 
        null=True, 
        blank=True 
    )

    age = models.IntegerField(
        verbose_name=_("Age"), 
        null=True, 
        blank=True,
        editable=False,
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

    last_seen_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Last seen"))

    @staticmethod
    def calculate_age(date_of_birth, on_date=None):
        """Calculate a person's age in completed years from their date of birth."""
        if not date_of_birth:
            return None
        on_date = on_date or date.today()
        return on_date.year - date_of_birth.year - (
            (on_date.month, on_date.day) < (date_of_birth.month, date_of_birth.day)
        )

    @property
    def is_online(self):
        """Presence is considered online for five minutes after the last heartbeat."""
        if not self.last_seen_at:
            return False
        return (timezone.now() - self.last_seen_at).total_seconds() <= 300

    def save(self, *args, **kwargs):
        self.age = self.calculate_age(self.date_of_birth) if self.date_of_birth else None
        super().save(*args, **kwargs)

    def __str__(self):
        f_name = self.first_name 
        l_name = self.last_name 
        if f_name or l_name: 
            return f"{f_name} {l_name}".strip() 
        return self.phone_number or self.email or f"User {self.pk}"


class PhoneOTP(models.Model):
    """One-time phone verification challenge; only a keyed digest is stored."""
    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"
        LOGIN = "login", "Login"

    phone_number = models.CharField(max_length=11, db_index=True, validators=[User.validation_iran_phone_number])
    purpose = models.CharField(max_length=10, choices=Purpose.choices)
    code_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_consumed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.phone_number} ({self.created_at:%Y-%m-%d %H:%M})"


class UserEmailBackend:
    """Authenticate email/password accounts without changing Django's phone USERNAME_FIELD."""
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        identifier = email or username
        if not identifier or not password or "@" not in identifier:
            return None
        try:
            user = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            # Run a dummy hash to reduce account enumeration timing differences.
            User().set_password(password)
            return None
        return user if user.check_password(password) and self.user_can_authenticate(user) else None

    @staticmethod
    def user_can_authenticate(user):
        return getattr(user, "is_active", True)
    
class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
