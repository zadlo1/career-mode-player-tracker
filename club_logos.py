import base64
import hashlib
import io
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from PIL import Image

LOGO_DIR = Path(__file__).parent / "data" / "images" / "clubs"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SIZE = 128

_SPECIAL = {"ł": "l", "ø": "o", "đ": "d", "ß": "ss", "æ": "ae", "œ": "oe"}


def slugify(name: str) -> str:
    text = name.strip().lower()
    for char, replacement in _SPECIAL.items():
        text = text.replace(char, replacement)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if not slug:
        slug = "club-" + hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
    return slug


def find_logo(club: str):
    slug = slugify(club)
    for extension in (".png", ".svg"):
        path = LOGO_DIR / f"{slug}{extension}"
        if path.exists():
            return path
    return None


def delete_logo(club: str) -> bool:
    removed = False
    slug = slugify(club)
    for extension in (".png", ".svg"):
        path = LOGO_DIR / f"{slug}{extension}"
        if path.exists():
            path.unlink()
            removed = True
    return removed


def save_logo(club: str, data: bytes, filename: str) -> None:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Plik jest za duży (maksymalnie 2 MB).")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Obsługiwane formaty: PNG, JPG, WebP i SVG.")

    if extension == ".svg":
        text = data.decode("utf-8", errors="ignore")
        if "<svg" not in text.lower():
            raise ValueError("To nie wygląda na poprawny plik SVG.")
        target_extension = ".svg"
        content = data
    else:
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except Exception:
            raise ValueError("Nie udało się odczytać obrazka.")
        image = image.convert("RGBA")
        image.thumbnail((MAX_SIZE, MAX_SIZE))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        target_extension = ".png"
        content = buffer.getvalue()

    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    delete_logo(club)
    (LOGO_DIR / f"{slugify(club)}{target_extension}").write_bytes(content)


@lru_cache(maxsize=256)
def _data_uri(path: str, modified_ns: int) -> str:
    file = Path(path)
    mime = "image/svg+xml" if file.suffix == ".svg" else "image/png"
    encoded = base64.b64encode(file.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def logo_data_uri(club: str):
    path = find_logo(club)
    if path is None:
        return None
    return _data_uri(str(path), path.stat().st_mtime_ns)