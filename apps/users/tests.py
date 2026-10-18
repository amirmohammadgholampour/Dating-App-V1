from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import User


class IdentityVerificationAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password="test-password")
        self.admin = User.objects.create_user(
            email="admin@example.com", password="test-password", is_staff=True
        )
        self.client = APIClient()

    def tearDown(self):
        if self.user.identity_video:
            self.user.identity_video.storage.delete(self.user.identity_video.name)

    def test_upload_is_private_admin_only_and_not_returned_by_profile(self):
        video_bytes = b"0000ftypisomidentity-video"
        self.client.force_authenticate(self.user)
        uploaded = SimpleUploadedFile("id.mp4", video_bytes, content_type="video/mp4")
        response = self.client.post("/api/users/verification/video/", {"video": uploaded}, format="multipart")
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertTrue(self.user.identity_video.name.startswith(f"identity_verification/{self.user.pk}/"))
        self.assertTrue(self.user.identity_video.storage.exists(self.user.identity_video.name))
        with self.assertRaises(ValueError):
            self.user.identity_video.url

        profile = self.client.get("/api/users/profile/")
        self.assertEqual(profile.status_code, 200)
        self.assertFalse(any("identity_video" in key for key in profile.data["data"]))
        self.assertFalse(any("identity_verification" in str(value) for value in profile.data["data"].values()))
        self.assertIn("is_verified", profile.data["data"])

        denied = self.client.get(f"/api/users/admin/users/{self.user.pk}/identity-video/")
        self.assertEqual(denied.status_code, 403)

        self.client.force_authenticate(self.admin)
        streamed = self.client.get(f"/api/users/admin/users/{self.user.pk}/identity-video/")
        self.assertEqual(streamed.status_code, 200)
        self.assertEqual(streamed["Content-Type"], "video/mp4")
        self.assertEqual(b"".join(streamed.streaming_content), video_bytes)
        self.assertIn("no-store", streamed["Cache-Control"])

        self.client.patch(
            f"/api/users/admin/users/{self.user.pk}/verification/",
            {"is_verified": True},
            format="json",
        )
        self.user.refresh_from_db()
        previous_video_name = self.user.identity_video.name
        self.client.force_authenticate(self.user)
        replacement = self.client.post(
            "/api/users/verification/video/",
            {"video": SimpleUploadedFile("replacement.mp4", b"0000ftypisomnew-video", content_type="video/mp4")},
            format="multipart",
        )
        self.assertEqual(replacement.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)
        self.assertFalse(self.user.identity_video.storage.exists(previous_video_name))

    def test_video_upload_rejects_invalid_type_and_size(self):
        self.client.force_authenticate(self.user)
        invalid = self.client.post(
            "/api/users/verification/video/",
            {"video": SimpleUploadedFile("fake.mp4", b"not a video")},
            format="multipart",
        )
        self.assertEqual(invalid.status_code, 400)

        with override_settings(MAX_IDENTITY_VIDEO_SIZE=8):
            too_large = self.client.post(
                "/api/users/verification/video/",
                {"video": SimpleUploadedFile("large.mp4", b"0000ftyp" + b"x")},
                format="multipart",
            )
        self.assertEqual(too_large.status_code, 400)

    def test_only_admin_can_change_verification_and_profile_cannot_override_it(self):
        self.client.force_authenticate(self.user)
        ordinary_user = self.client.patch(
            f"/api/users/admin/users/{self.user.pk}/verification/",
            {"is_verified": True},
            format="json",
        )
        self.assertEqual(ordinary_user.status_code, 403)
        profile_update = self.client.patch(
            "/api/users/update/", {"is_verified": True}, format="json"
        )
        self.assertEqual(profile_update.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

        self.client.force_authenticate(self.admin)
        verified = self.client.patch(
            f"/api/users/admin/users/{self.user.pk}/verification/",
            {"is_verified": True},
            format="json",
        )
        self.assertEqual(verified.status_code, 200)
        self.assertTrue(verified.data["is_verified"])

        invalid = self.client.patch(
            f"/api/users/admin/users/{self.user.pk}/verification/",
            {"is_verified": "not-a-bool"},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)

        self.client.force_authenticate(self.user)
        unverified = self.client.patch(
            "/api/users/update/", {"identity_video": "somewhere.mp4"}, format="json"
        )
        self.assertEqual(unverified.status_code, 400)
