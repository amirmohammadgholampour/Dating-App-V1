# Generated for the Discover suggestion history model.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscoverySuggestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_suggested_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='First suggested at')),
                ('last_suggested_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Last suggested at')),
                ('display_count', models.PositiveIntegerField(default=1, verbose_name='Display count')),
                ('last_position', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Last position')),
                ('suggested_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discover_impressions', to=settings.AUTH_USER_MODEL, verbose_name='Suggested user')),
                ('viewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discovery_suggestions', to=settings.AUTH_USER_MODEL, verbose_name='Viewer')),
            ],
            options={
                'verbose_name': 'Discovery suggestion',
                'verbose_name_plural': 'Discovery suggestions',
                'ordering': ['-last_suggested_at'],
                'indexes': [
                    models.Index(fields=['viewer', '-last_suggested_at'], name='matching_ds_viewer_last_idx'),
                    models.Index(fields=['suggested_user', '-last_suggested_at'], name='matching_ds_user_last_idx'),
                ],
                'constraints': [
                    models.UniqueConstraint(fields=('viewer', 'suggested_user'), name='matching_discovery_unique_pair'),
                ],
            },
        ),
    ]
