import apps.users.db.user_model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=11, null=True, unique=True,
                                   validators=[apps.users.db.user_model.User.validation_iran_phone_number],
                                   verbose_name='Phone number'),
        ),
        migrations.AddField(
            model_name='user', name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name='Email address'),
        ),
        migrations.AddField(
            model_name='user', name='date_of_birth',
            field=models.DateField(blank=True, null=True, verbose_name='Date of birth'),
        ),
        migrations.AddField(
            model_name='user', name='last_seen_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Last seen'),
        ),
        migrations.AlterField(
            model_name='user', name='age',
            field=models.IntegerField(blank=True, editable=False, null=True, verbose_name='Age'),
        ),
        migrations.CreateModel(
            name='PhoneOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(db_index=True, max_length=11,
                    validators=[apps.users.db.user_model.User.validation_iran_phone_number])),
                ('purpose', models.CharField(choices=[('register', 'Register'), ('login', 'Login')], max_length=10)),
                ('code_digest', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('is_consumed', models.BooleanField(default=False)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
