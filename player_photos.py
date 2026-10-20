import io
from pathlib import Path

from PIL import Image

from club_logos import MAX_UPLOAD_BYTES, _data_uri

PHOTO_DIR = Path(__file__).parent / "data" / "images" / "players"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_SIZE = 256


def _photo_path(player_id) -> Path:
    return PHOTO_DIR / f"{int(player_id)}.png"


def find_photo(player_id):
    path = _photo_path(player_id)
    return path if path.exists() else None


def delete_photo(player_id) -> bool:
    path = _photo_path(player_id)
    if path.exists():
        path.unlink()
        return True
    return False


def save_photo(player_id, data: bytes, filename: str) -> None:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Plik jest za duży (maksymalnie 2 MB).")

    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Obsługiwane formaty: PNG, JPG i WebP.")

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception:
        raise ValueError("Nie udało się odczytać obrazka.")
    image = image.convert("RGBA")
    image.thumbnail((MAX_SIZE, MAX_SIZE))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)

    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    _photo_path(player_id).write_bytes(buffer.getvalue())


def photo_data_uri(player_id):
    path = find_photo(player_id)
    if path is None:
        return None
    return _data_uri(str(path), path.stat().st_mtime_ns)
