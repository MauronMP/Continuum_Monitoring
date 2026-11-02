from __future__ import annotations

import http.client
import json
from time import monotonic, sleep
from urllib.parse import urlsplit


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = 120,
) -> dict:
    parsed = urlsplit(url)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError(f"Unsupported benchmark endpoint: {url}")
    deadline = None if timeout is None else monotonic() + timeout

    def remaining() -> float | None:
        if deadline is None:
            return None
        value = deadline - monotonic()
        if value <= 0:
            raise TimeoutError(f"{url}: global request deadline exceeded")
        return value

    connection = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=remaining())
    try:
        connection.request(method, parsed.path or "/", body=payload, headers=headers or {})
        if connection.sock is not None:
            connection.sock.settimeout(remaining())
        response = connection.getresponse()
        chunks = []
        while True:
            if connection.sock is not None:
                connection.sock.settimeout(remaining())
            chunk = response.read1(64 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            remaining()
        body = b"".join(chunks)
        if not 200 <= response.status < 300:
            detail = body.decode("utf-8", errors="replace")
            raise RuntimeError(f"{url}: HTTP {response.status}: {detail}")
        return json.loads(body)
    except (OSError, TimeoutError, http.client.HTTPException) as error:
        raise RuntimeError(f"{url}: {error}") from error
    finally:
        connection.close()


def wait_ready(
    endpoint: str, *, deadline_seconds: float, require_idle: bool = False, expected: dict[str, object] | None = None
) -> dict:
    deadline = monotonic() + deadline_seconds
    last_error = "no response"
    while monotonic() < deadline:
        try:
            health = request_json(f"{endpoint}/health", timeout=min(5, deadline_seconds))
            compatible = (
                health.get("service") == "continuum-worker"
                and health.get("protocol_version") == "continuum-rdf-worker-v1"
            )
            matches = all(health.get(key) == value for key, value in (expected or {}).items())
            idle = not require_idle or (
                health.get("idle") is True and health.get("active_requests") == 0 and health.get("queue_depth") == 0
            )
            if health.get("status") == "ready" and compatible and matches and idle:
                return health
            last_error = f"ready={compatible} assets={matches} idle={idle}"
        except RuntimeError as error:
            last_error = str(error)
        sleep(0.5)
    raise TimeoutError(f"{endpoint} did not become ready: {last_error}")
