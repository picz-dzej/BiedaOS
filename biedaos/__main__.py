import socket
import threading
import webbrowser

import uvicorn

from .app import create_app


def free_port(start: int = 8137) -> int:
    for port in range(start, start + 50):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Brak wolnego portu.")


def main() -> None:
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    print(f"BiedaOS działa pod adresem {url}")
    print("Zamknij to okno, żeby wyłączyć aplikację.")
    threading.Timer(1.0, webbrowser.open, [url]).start()
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
