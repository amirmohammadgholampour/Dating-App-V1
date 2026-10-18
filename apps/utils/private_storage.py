from django.core.files.storage import FileSystemStorage
from django.conf import settings


class PrivateFileSystemStorage(FileSystemStorage):
    """Local storage whose files are only served through permission checked views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", settings.PRIVATE_MEDIA_ROOT)
        super().__init__(*args, **kwargs)

    def url(self, name):
        raise ValueError("Private files do not have public URLs.")


private_file_storage = PrivateFileSystemStorage()
