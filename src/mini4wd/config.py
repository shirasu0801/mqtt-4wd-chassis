from __future__ import annotations

import os
import socket
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


@dataclass(frozen=True)
class MqttConfig:
    host: str
    port: int
    username: str | None
    password: str | None
    control_topic: str
    status_topic: str
    qos: int
    keepalive: int
    vehicle_client_id: str
    controller_client_id: str


@dataclass(frozen=True)
class MotorConfig:
    ain1_pin: int
    ain2_pin: int
    pwm_frequency_hz: int


@dataclass(frozen=True)
class RuntimeConfig:
    mqtt: MqttConfig
    motor: MotorConfig
    failsafe_timeout_s: float
    simulation_mode: bool


def load_config() -> RuntimeConfig:
    hostname = socket.gethostname()
    mqtt = MqttConfig(
        host=os.getenv("MQTT_HOST", "localhost"),
        port=_env_int("MQTT_PORT", 1883),
        username=os.getenv("MQTT_USERNAME"),
        password=os.getenv("MQTT_PASSWORD"),
        control_topic=os.getenv("MQTT_CONTROL_TOPIC", "mini4wd/control"),
        status_topic=os.getenv("MQTT_STATUS_TOPIC", "mini4wd/status"),
        qos=_env_int("MQTT_QOS", 1),
        keepalive=_env_int("MQTT_KEEPALIVE", 30),
        vehicle_client_id=os.getenv("MQTT_VEHICLE_CLIENT_ID", f"mini4wd-vehicle-{hostname}"),
        controller_client_id=os.getenv("MQTT_CONTROLLER_CLIENT_ID", f"mini4wd-controller-{hostname}"),
    )
    motor = MotorConfig(
        ain1_pin=_env_int("MOTOR_AIN1_PIN", 17),
        ain2_pin=_env_int("MOTOR_AIN2_PIN", 27),
        pwm_frequency_hz=_env_int("MOTOR_PWM_FREQ_HZ", 1000),
    )
    return RuntimeConfig(
        mqtt=mqtt,
        motor=motor,
        failsafe_timeout_s=_env_float("FAILSAFE_TIMEOUT_S", 1.0),
        simulation_mode=os.getenv("MINI4WD_SIMULATION", "0") == "1",
    )

