from __future__ import annotations

import json
from typing import Any

from risk_dashboard.platform.ai_runtime.contracts import StreamEvent


def format_sse_event(event: StreamEvent) -> str:
    """Format a StreamEvent as a standard Server-Sent Event (SSE) frame."""
    payload = event.model_dump_json()
    return f"event: {event.event}\ndata: {payload}\n\n"


def parse_sse_frame(frame: str) -> dict[str, Any] | None:
    """Parse an individual SSE frame for test validation and client consumption."""
    event_type = "message"
    data_lines = []
    for line in frame.strip().splitlines():
        if line.startswith("event:"):
            event_type = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())
    if not data_lines:
        return None
    raw_data = "\n".join(data_lines)
    try:
        parsed_data = json.loads(raw_data)
    except json.JSONDecodeError:
        parsed_data = raw_data
    return {"event": event_type, "data": parsed_data}

