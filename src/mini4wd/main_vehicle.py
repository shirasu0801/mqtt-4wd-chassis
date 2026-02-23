from __future__ import annotations

import argparse
import logging

from .config import load_config
from .motor import DRV8833MotorDriver, MockMotorDriver
from .vehicle import VehicleService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MQTT mini4wd vehicle subscriber")
    parser.add_argument("--simulation", action="store_true", help="use mock motor driver")
    parser.add_argument("--log-level", default="INFO", help="logging level (default: INFO)")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config()
    simulation = args.simulation or cfg.simulation_mode

    if simulation:
        motor = MockMotorDriver()
    else:
        motor = DRV8833MotorDriver(
            ain1_pin=cfg.motor.ain1_pin,
            ain2_pin=cfg.motor.ain2_pin,
            pwm_frequency_hz=cfg.motor.pwm_frequency_hz,
        )

    service = VehicleService(cfg, motor)
    try:
        service.run()
    except KeyboardInterrupt:
        pass
    finally:
        service.shutdown()


if __name__ == "__main__":
    main()

