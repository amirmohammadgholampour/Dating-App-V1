from django.db import models 
from django.contrib.auth.models import AbstractUser 
from django.utils import timezone 
from jdatetime import date as jdate

class User(AbstractUser): 
    class Gender(models.TextChoices): 
        MALE = "male" 
        FEMALE = "female" 
        OTHER = "other" 
    
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", 
        verbose_name="Profile picture", 
        null=True, 
        blank=True 
    )

    date_of_birth = models.DateField(
        verbose_name="Birth date", 
        null=True, 
        blank=True 
    )

    gender = models.CharField(
        max_length=255, 
        choices=Gender.choices, 
        verbose_name="Gender", 
        default=Gender.MALE 
    ) 

    city = models.CharField(
        max_length=255, 
        verbose_name="City", 
    )

    bio = models.TextField(
        max_length=500, 
        verbose_name="Biography", 
        blank=True 
    )

    # interests = models.ManyToManyField(
    #     'Interest',
    #     through='UserInterest',
    #     verbose_name='Interests'
    # ) 

    def __str__(self):
        f_name = self.first_name 
        l_name = self.last_name 
        if f_name or l_name: 
            return f"{f_name} {l_name}".strip() 
        return self.username 
    
    @property
    def age(self):
        if not self.date_of_birth:
            return None

        today_gregorian = timezone.now().date()
        today_jalali = jdate.fromgregorian(date=today_gregorian)

        birth_jalali = jdate.fromgregorian(date=self.date_of_birth)

        age = today_jalali.year - birth_jalali.year
        if (today_jalali.month, today_jalali.day) < (birth_jalali.month, birth_jalali.day):
            age -= 1
        return age