from __future__ import annotations

import argparse
import uuid

from .config import load_config
from .controller import ControllerClient


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MQTT mini4wd command publisher")
    parser.add_argument(
        "action",
        choices=["forward", "reverse", "stop", "estop"],
        help="vehicle action",
    )
    parser.add_argument("--speed", type=int, default=0, help="speed 0-100")
    parser.add_argument(
        "--stop-mode",
        choices=["coast", "brake"],
        default="coast",
        help="stop mode for stop/estop",
    )
    parser.add_argument(
        "--request-id",
        default=None,
        help="optional request id (default auto-generate)",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    cfg = load_config()
    client = ControllerClient(cfg)
    request_id = args.request_id or str(uuid.uuid4())
    client.send(
        action=args.action,
        speed=args.speed,
        stop_mode=args.stop_mode,
        request_id=request_id,
    )
    print(
        f"published action={args.action} speed={args.speed} "
        f"stop_mode={args.stop_mode} request_id={request_id}"
    )


if __name__ == "__main__":
    main()

