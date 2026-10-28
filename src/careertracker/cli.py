import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="careertracker", description="Uruchamia Career Mode Tracker."
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="adres nasłuchiwania (domyślnie 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8000, help="port (domyślnie 8000)")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="przeładowanie po zmianie kodu (do pracy nad aplikacją)",
    )
    args = parser.parse_args()

    uvicorn.run(
        "careertracker.web.app:app", host=args.host, port=args.port, reload=args.reload
    )