from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auth_profile_and_presence'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_verified',
            field=models.BooleanField(default=False, verbose_name='Phone verified'),
        ),
    ]
