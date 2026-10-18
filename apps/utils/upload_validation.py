from pathlib import Path
import zipfile

from django.conf import settings
from PIL import Image, UnidentifiedImageError


def _header(uploaded_file, length=16):
    position = uploaded_file.tell()
    try:
        return uploaded_file.read(length)
    finally:
        uploaded_file.seek(position)


def validate_identity_video(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    if uploaded_file.size > settings.MAX_IDENTITY_VIDEO_SIZE:
        raise ValueError("Identity videos must be 50 MB or smaller.")

    header = _header(uploaded_file, 12)
    valid = (
        (extension in {".mp4", ".mov", ".3gp"} and header[4:8] == b"ftyp")
        or (extension == ".webm" and header.startswith(b"\x1a\x45\xdf\xa3"))
    )
    if not valid:
        raise ValueError("Upload a valid MP4, MOV, 3GP, or WebM video.")
    return {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".3gp": "video/3gpp",
        ".webm": "video/webm",
    }[extension]


def validate_chat_attachment(uploaded_file, message_type):
    extension = Path(uploaded_file.name).suffix.lower()
    if message_type == "image":
        if uploaded_file.size > settings.MAX_CHAT_IMAGE_SIZE:
            raise ValueError("Images must be 10 MB or smaller.")
        try:
            image = Image.open(uploaded_file)
            image_format = image.format
            image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            raise ValueError("Upload a valid JPEG, PNG, GIF, or WebP image.")
        finally:
            uploaded_file.seek(0)
        formats = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".gif": "GIF", ".webp": "WEBP"}
        if extension not in formats or image_format != formats[extension]:
            raise ValueError("Image extension and file contents must match (JPEG, PNG, GIF, or WebP).")
        return f"image/{'jpeg' if image_format == 'JPEG' else image_format.lower()}"

    if message_type == "voice":
        if uploaded_file.size > settings.MAX_CHAT_VOICE_SIZE:
            raise ValueError("Voice messages must be 20 MB or smaller.")
        header = _header(uploaded_file, 16)
        signatures = {
            ".mp3": header.startswith(b"ID3") or (len(header) > 1 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0),
            ".wav": header.startswith(b"RIFF") and header[8:12] == b"WAVE",
            ".m4a": header[4:8] == b"ftyp" and header[8:12] in {b"M4A ", b"M4B ", b"isom", b"mp42"},
            ".aac": len(header) > 1 and header[0] == 0xFF and header[1] & 0xF6 == 0xF0,
            ".ogg": header.startswith(b"OggS"),
            ".opus": header.startswith(b"OggS"),
            ".webm": header.startswith(b"\x1a\x45\xdf\xa3"),
        }
        if not signatures.get(extension, False):
            raise ValueError("Upload a valid MP3, WAV, M4A, AAC, OGG, OPUS, or WebM audio file.")
        return {
            ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4",
            ".aac": "audio/aac", ".ogg": "audio/ogg", ".opus": "audio/ogg", ".webm": "audio/webm",
        }[extension]

    if message_type == "file":
        if uploaded_file.size > settings.MAX_CHAT_FILE_SIZE:
            raise ValueError("Attachments must be 25 MB or smaller.")
        header = _header(uploaded_file, 8)
        if extension == ".pdf" and header.startswith(b"%PDF-"):
            return "application/pdf"
        if extension in {".txt", ".csv", ".md"}:
            position = uploaded_file.tell()
            try:
                content = uploaded_file.read()
                if b"\x00" in content:
                    raise ValueError("Text attachments must contain valid UTF-8 text.")
                content.decode("utf-8-sig")
            except UnicodeDecodeError:
                raise ValueError("Text attachments must contain valid UTF-8 text.")
            finally:
                uploaded_file.seek(position)
            return {".txt": "text/plain", ".csv": "text/csv", ".md": "text/markdown"}[extension]

        office_members = {
            ".docx": "word/document.xml",
            ".xlsx": "xl/workbook.xml",
            ".pptx": "ppt/presentation.xml",
        }
        if extension in office_members and header.startswith(b"PK"):
            position = uploaded_file.tell()
            try:
                with zipfile.ZipFile(uploaded_file) as archive:
                    members = archive.namelist()
                    if "[Content_Types].xml" in members and office_members[extension] in members:
                        return {
                            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        }[extension]
            except (OSError, zipfile.BadZipFile):
                pass
            finally:
                uploaded_file.seek(position)

        if extension in {".doc", ".xls", ".ppt"} and header == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            return {
                ".doc": "application/msword",
                ".xls": "application/vnd.ms-excel",
                ".ppt": "application/vnd.ms-powerpoint",
            }[extension]
        raise ValueError("Upload a valid PDF, text, CSV, Markdown, or Office document.")

    raise ValueError("Unsupported message type.")
