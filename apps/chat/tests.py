from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.chat.models import Conversation, Message
from apps.safety.models import Block
from apps.users.models import User


class ChatMessageFeatureTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="alice@example.com", password="test-password")
        self.bob = User.objects.create_user(email="bob@example.com", password="test-password")
        self.eve = User.objects.create_user(email="eve@example.com", password="test-password")
        self.conversation = Conversation.objects.create(user1=self.alice, user2=self.bob)
        self.client = APIClient()

    def tearDown(self):
        for message in Message.objects.exclude(attachment="").exclude(attachment__isnull=True):
            message.attachment.storage.delete(message.attachment.name)

    def _send(self, user, data, conversation=None):
        self.client.force_authenticate(user)
        return self.client.post(
            f"/api/chat/conversations/{(conversation or self.conversation).pk}/send/",
            data,
            format="multipart" if any(hasattr(value, "read") for value in data.values()) else "json",
        )

    @staticmethod
    def _png_upload(name="picture.png"):
        image_bytes = BytesIO()
        Image.new("RGB", (2, 2), color="red").save(image_bytes, format="PNG")
        return SimpleUploadedFile(name, image_bytes.getvalue(), content_type="image/png")

    def test_text_message_and_pin_unpin(self):
        sent = self._send(self.alice, {"content": "Hello"})
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(sent.data["data"]["message_type"], Message.Type.TEXT)
        self.assertFalse(sent.data["data"]["is_pinned"])
        message_id = sent.data["data"]["id"]

        pinned = self.client.post(
            f"/api/chat/conversations/{self.conversation.pk}/messages/{message_id}/pin/", {}, format="json"
        )
        self.assertEqual(pinned.status_code, 200)
        self.assertTrue(pinned.data["is_pinned"])
        self.assertTrue(self.client.get(f"/api/chat/conversations/{self.conversation.pk}/messages/").data["results"][0]["is_pinned"])

        unpinned = self.client.delete(
            f"/api/chat/conversations/{self.conversation.pk}/messages/{message_id}/pin/"
        )
        self.assertEqual(unpinned.status_code, 200)
        self.assertFalse(unpinned.data["is_pinned"])

    def test_pin_checks_conversation_membership_and_message_conversation(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.alice, content="Hello")
        self.client.force_authenticate(self.eve)
        denied = self.client.post(
            f"/api/chat/conversations/{self.conversation.pk}/messages/{message.pk}/pin/"
        )
        self.assertEqual(denied.status_code, 403)

        other_conversation = Conversation.objects.create(user1=self.bob, user2=self.eve)
        other_message = Message.objects.create(conversation=other_conversation, sender=self.bob, content="Private")
        self.client.force_authenticate(self.alice)
        mismatch = self.client.post(
            f"/api/chat/conversations/{self.conversation.pk}/messages/{other_message.pk}/pin/"
        )
        self.assertEqual(mismatch.status_code, 404)
        self.assertFalse(other_message.is_pinned)

    def test_image_voice_and_file_uploads_are_typed_and_private(self):
        image_response = self._send(self.alice, {"message_type": "image", "attachment": self._png_upload()})
        self.assertEqual(image_response.status_code, 201)
        image_data = image_response.data["data"]
        self.assertEqual(image_data["message_type"], Message.Type.IMAGE)
        self.assertTrue(image_data["attachment_url"].endswith(f"/messages/{image_data['id']}/media/"))

        audio_response = self._send(
            self.bob,
            {"message_type": "voice", "attachment": SimpleUploadedFile("voice.mp3", b"ID3\x04\x00\x00audio")},
        )
        self.assertEqual(audio_response.status_code, 201)
        self.assertEqual(audio_response.data["data"]["message_type"], Message.Type.VOICE)

        webm_response = self._send(
            self.alice,
            {"message_type": "voice", "attachment": SimpleUploadedFile("recording.webm", b"\x1a\x45\xdf\xa3audio")},
        )
        self.assertEqual(webm_response.status_code, 201)
        self.assertEqual(webm_response.data["data"]["message_type"], Message.Type.VOICE)

        file_response = self._send(
            self.alice,
            {"message_type": "file", "attachment": SimpleUploadedFile("notes.pdf", b"%PDF-1.7 content")},
        )
        self.assertEqual(file_response.status_code, 201)
        file_data = file_response.data["data"]
        self.assertEqual(file_data["message_type"], Message.Type.FILE)

        self.client.force_authenticate(self.bob)
        downloaded = self.client.get(file_data["attachment_url"])
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(b"".join(downloaded.streaming_content), b"%PDF-1.7 content")
        self.assertIn("attachment", downloaded["Content-Disposition"])

        self.client.force_authenticate(self.eve)
        denied = self.client.get(file_data["attachment_url"])
        self.assertEqual(denied.status_code, 403)

        self.client.force_authenticate(self.alice)
        listed = self.client.get(f"/api/chat/conversations/{self.conversation.pk}/messages/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual({m["message_type"] for m in listed.data["results"]}, {"image", "voice", "file"})

    def test_invalid_attachment_types_sizes_and_missing_files_are_rejected(self):
        invalid = self._send(
            self.alice,
            {"message_type": "image", "attachment": SimpleUploadedFile("bad.png", b"not an image")},
        )
        self.assertEqual(invalid.status_code, 400)

        missing = self._send(self.alice, {"message_type": "voice"})
        self.assertEqual(missing.status_code, 400)

        with override_settings(MAX_CHAT_FILE_SIZE=3):
            too_large = self._send(
                self.alice,
                {"message_type": "file", "attachment": SimpleUploadedFile("large.pdf", b"%PDF-1.7")},
            )
        self.assertEqual(too_large.status_code, 400)

        unsupported = self._send(
            self.alice,
            {"message_type": "file", "attachment": SimpleUploadedFile("run.exe", b"MZ executable")},
        )
        self.assertEqual(unsupported.status_code, 400)

    def test_either_direction_of_block_stops_messages_and_hides_conversation(self):
        Block.objects.create(blocker=self.bob, blocked=self.alice)
        self.client.force_authenticate(self.alice)

        sent = self.client.post(
            f"/api/chat/conversations/{self.conversation.pk}/send/",
            {"content": "Should not send"},
            format="json",
        )
        self.assertEqual(sent.status_code, 403)
        self.assertEqual(self.client.get(f"/api/chat/conversations/{self.conversation.pk}/messages/").status_code, 403)
        self.assertEqual(self.client.get("/api/chat/conversations/").data["count"], 0)

        self.client.force_authenticate(self.bob)
        reverse_direction = self.client.post(
            f"/api/chat/conversations/{self.conversation.pk}/send/",
            {"content": "Also blocked"},
            format="json",
        )
        self.assertEqual(reverse_direction.status_code, 403)
        self.assertEqual(Message.objects.count(), 0)

    def test_non_members_cannot_download_attachment(self):
        sent = self._send(self.alice, {"message_type": "image", "attachment": self._png_upload()})
        self.client.force_authenticate(self.eve)
        response = self.client.get(sent.data["data"]["attachment_url"])
        self.assertEqual(response.status_code, 403)
