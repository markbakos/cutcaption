"""JSON metadata exporter."""

from __future__ import annotations

import json

from cutcaption.models import Caption


def render_json(captions: list[Caption] | tuple[Caption, ...]) -> str:
    payload = [
        {"text": caption.text, "start": caption.start, "end": caption.end}
        for caption in captions
    ]
    return json.dumps(payload, indent=2) + "\n"
