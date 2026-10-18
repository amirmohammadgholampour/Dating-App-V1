from django.test import TestCase
from rest_framework.test import APIClient

from apps.safety.models import Block
from apps.users.models import User


class BlockAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="blocker@example.com", password="test-password")
        self.other = User.objects.create_user(email="blocked@example.com", password="test-password", first_name="Other")
        self.client = APIClient()

    def test_block_list_and_unblock_are_scoped_to_authenticated_user(self):
        response = self.client.get("/api/safety/blocks/")
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(self.user)
        response = self.client.post("/api/safety/blocks/", {"user_id": self.other.pk}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["user_id"], self.other.pk)

        duplicate = self.client.post("/api/safety/blocks/", {"user_id": self.other.pk}, format="json")
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(Block.objects.filter(blocker=self.user, blocked=self.other).count(), 1)

        listed = self.client.get("/api/safety/blocks/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([row["user_id"] for row in listed.data], [self.other.pk])

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/safety/blocks/").data, [])
        not_owned = self.client.delete(f"/api/safety/blocks/{self.other.pk}/")
        self.assertEqual(not_owned.status_code, 404)

        self.client.force_authenticate(self.user)
        unblocked = self.client.delete(f"/api/safety/blocks/{self.other.pk}/")
        self.assertEqual(unblocked.status_code, 200)
        self.assertFalse(Block.objects.filter(blocker=self.user, blocked=self.other).exists())

    def test_cannot_block_self_or_unknown_users(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(
            self.client.post("/api/safety/blocks/", {"user_id": self.user.pk}, format="json").status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/safety/blocks/", {"user_id": 999999}, format="json").status_code,
            400,
        )
        self.assertEqual(Block.objects.count(), 0)
