from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


VALID_ACTIONS = {"forward", "reverse", "stop", "estop"}
VALID_STOP_MODES = {"coast", "brake"}


@dataclass(frozen=True)
class ControlMessage:
    action: str
    speed: int = 0
    stop_mode: str = "coast"
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

    @staticmethod
    def from_payload(payload: bytes) -> "ControlMessage":
        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid payload: {exc}") from exc
        return ControlMessage.from_dict(data)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ControlMessage":
        action = str(data.get("action", "")).lower()
        if action not in VALID_ACTIONS:
            raise ValueError(f"invalid action: {action}")

        speed_raw = data.get("speed", 0)
        try:
            speed = int(speed_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid speed: {speed_raw}") from exc
        if speed < 0 or speed > 100:
            raise ValueError(f"speed out of range: {speed}")

        stop_mode = str(data.get("stop_mode", "coast")).lower()
        if stop_mode not in VALID_STOP_MODES:
            raise ValueError(f"invalid stop_mode: {stop_mode}")

        request_id = data.get("request_id")
        if request_id is not None:
            request_id = str(request_id)

        timestamp = data.get("timestamp")
        if timestamp is not None:
            timestamp = str(timestamp)

        return ControlMessage(
            action=action,
            speed=speed,
            stop_mode=stop_mode,
            request_id=request_id,
            timestamp=timestamp,
        )


def build_status_payload(
    *,
    state: str,
    speed: int,
    reason: str,
    request_id: Optional[str] = None,
) -> str:
    payload: dict[str, Any] = {
        "state": state,
        "speed": speed,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if request_id:
        payload["request_id"] = request_id
    return json.dumps(payload, ensure_ascii=True)


def build_control_payload(
    *,
    action: str,
    speed: int = 0,
    stop_mode: str = "coast",
    request_id: Optional[str] = None,
) -> str:
    if action not in VALID_ACTIONS:
        raise ValueError(f"invalid action: {action}")
    if speed < 0 or speed > 100:
        raise ValueError(f"speed out of range: {speed}")
    if stop_mode not in VALID_STOP_MODES:
        raise ValueError(f"invalid stop_mode: {stop_mode}")

    payload: dict[str, Any] = {
        "action": action,
        "speed": speed,
        "stop_mode": stop_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if request_id:
        payload["request_id"] = request_id
    return json.dumps(payload, ensure_ascii=True)

