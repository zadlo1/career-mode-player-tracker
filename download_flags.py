import urllib.request
from pathlib import Path

from countries import COUNTRIES

BASE = "https://raw.githubusercontent.com/lipis/flag-icons/main"
TARGET = Path(__file__).parent / "assets" / "flags"


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "career-db-flag-downloader"})
    with urllib.request.urlopen(request, timeout=30) as response:
        path.write_bytes(response.read())


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    failed = []
    downloaded = 0

    for code in COUNTRIES:
        path = TARGET / f"{code.lower()}.svg"
        if path.exists():
            continue
        try:
            download(f"{BASE}/flags/4x3/{code.lower()}.svg", path)
            downloaded += 1
        except Exception as error:
            failed.append((code, str(error)))

    license_path = TARGET / "LICENSE-flag-icons.txt"
    if not license_path.exists():
        download(f"{BASE}/LICENSE", license_path)

    print(f"Pobrano: {downloaded}, razem krajów: {len(COUNTRIES)}")
    if failed:
        print("Nie udało się pobrać:")
        for code, error in failed:
            print(f"  {code}: {error}")
    else:
        print("Wszystkie flagi są na miejscu.")


if __name__ == "__main__":
    main()