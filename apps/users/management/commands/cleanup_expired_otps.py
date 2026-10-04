from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.users.db.user_model import PhoneOTP


class Command(BaseCommand):
    help = "Delete expired phone OTP challenges and consumed challenges older than one day."

    def handle(self, *args, **options):
        now = timezone.now()
        old_consumed = now - timedelta(days=1)
        deleted_count, _ = PhoneOTP.objects.filter(
            Q(expires_at__lte=now) | Q(is_consumed=True, created_at__lte=old_consumed)
        ).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} expired OTP records."))
