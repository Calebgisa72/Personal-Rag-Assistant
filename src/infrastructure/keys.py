from __future__ import annotations

import hashlib
import json
from typing import Any


def make_key(scope: str, *parts: Any, version: str = "v1") -> str:
    """Generate a key for caching or storage."""

    # Turn the parts into a stable string representation
    payload = json.dumps(parts, default=str, sort_keys=True, separators=(',', ':'))

    # Create a hash of the string
    digest = hashlib.sha256(payload.encode()).hexdigest()

    # Return a namespaced key with a version
    return f"{version}:{scope}:{digest}"
