"""Probe a participant-authorized model endpoint without exposing credentials.

This intentionally has no model or endpoint default. It is not a mock and it
does not prove access until all required environment variables are provided.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request


REQUIRED = ("QOR_MODEL_ENDPOINT", "QOR_MODEL_ID", "QOR_MODEL_API_KEY")


def main() -> int:
    missing = [name for name in REQUIRED if not os.getenv(name)]
    if missing:
        print("not run: missing participant entitlement variables: " + ", ".join(missing))
        return 2

    endpoint = os.environ["QOR_MODEL_ENDPOINT"]
    model_id = os.environ["QOR_MODEL_ID"]
    # OpenAI-compatible Responses body. Run only when this is the organizer's
    # documented API shape; adapt the script if its documented provider differs.
    payload = {"model": model_id, "input": "Reply with exactly: QOR smoke test"}
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['QOR_MODEL_API_KEY']}",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            print(json.dumps({
                "status": response.status,
                "model_id": model_id,
                "latency_ms": elapsed_ms,
                "answer_sha256": hashlib.sha256(raw).hexdigest(),
                "tool_request": "not attempted by generic probe; requires documented provider tool schema",
            }))
            return 0
    except urllib.error.HTTPError as exc:
        print(json.dumps({"status": exc.code, "model_id": model_id, "error": "HTTP error (body redacted)"}))
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({"model_id": model_id, "error": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
