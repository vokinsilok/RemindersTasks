import os
import socket
import time
from urllib.parse import urlparse


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    if not host:
        raise RuntimeError("DATABASE_URL host is required")

    deadline = time.monotonic() + 60
    last_error: OSError | None = None

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"Database is reachable at {host}:{port}", flush=True)
                return
        except OSError as exc:
            last_error = exc
            print(f"Waiting for database at {host}:{port}: {exc}", flush=True)
            time.sleep(2)

    raise TimeoutError(f"Database is not reachable at {host}:{port}: {last_error}")


if __name__ == "__main__":
    main()
