"""Profile helpers."""

from __future__ import annotations

import hashlib
import json


def profile_hash(profile: dict) -> str:
    payload = json.dumps(profile, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
