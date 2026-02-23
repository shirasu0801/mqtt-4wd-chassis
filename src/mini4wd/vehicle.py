from __future__ import annotations

import logging
import threading
import time

from paho.mqtt import client as mqtt

from .config import RuntimeConfig
from .motor import BaseMotorDriver
from .protocol import ControlMessage, build_status_payload


logger = logging.getLogger(__name__)


class VehicleService:
    def __init__(self, config: RuntimeConfig, motor: BaseMotorDriver) -> None:
        self._cfg = config
        self._motor = motor
        self._last_command_at = time.monotonic()
        self._lock = threading.Lock()
        self._running = False
        self._timed_out = False
        self._state = "stop"
        self._speed = 0

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.mqtt.vehicle_client_id,
            protocol=mqtt.MQTTv311,
        )
        if config.mqtt.username:
            self._client.username_pw_set(config.mqtt.username, config.mqtt.password)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def _on_connect(self, client: mqtt.Client, _userdata, _flags, reason_code, _properties) -> None:
        if reason_code != 0:
            logger.error("MQTT connect failed: %s", reason_code)
            return
        logger.info("MQTT connected. subscribe topic=%s", self._cfg.mqtt.control_topic)
        client.subscribe(self._cfg.mqtt.control_topic, qos=self._cfg.mqtt.qos)

    def _on_message(self, _client: mqtt.Client, _userdata, msg: mqtt.MQTTMessage) -> None:
        try:
            command = ControlMessage.from_payload(msg.payload)
        except ValueError as exc:
            logger.warning("invalid control message: %s", exc)
            return

        with self._lock:
            self._last_command_at = time.monotonic()
            self._timed_out = False

        if command.action == "forward":
            self._motor.forward(command.speed)
            self._state = "forward"
            self._speed = command.speed
            self._publish_status("command", command.request_id)
            return

        if command.action == "reverse":
            self._motor.reverse(command.speed)
            self._state = "reverse"
            self._speed = command.speed
            self._publish_status("command", command.request_id)
            return

        if command.action == "stop":
            self._motor.stop(command.stop_mode)
            self._state = "stop"
            self._speed = 0
            self._publish_status("command", command.request_id)
            return

        if command.action == "estop":
            stop_mode = command.stop_mode if command.stop_mode in {"coast", "brake"} else "brake"
            self._motor.stop(stop_mode)
            self._state = "stop"
            self._speed = 0
            self._publish_status("emergency_stop", command.request_id)

    def _publish_status(self, reason: str, request_id: str | None = None) -> None:
        payload = build_status_payload(
            state=self._state,
            speed=self._speed,
            reason=reason,
            request_id=request_id,
        )
        self._client.publish(
            self._cfg.mqtt.status_topic,
            payload=payload,
            qos=self._cfg.mqtt.qos,
            retain=False,
        )

    def run(self) -> None:
        self._running = True
        self._client.connect(
            self._cfg.mqtt.host,
            self._cfg.mqtt.port,
            self._cfg.mqtt.keepalive,
        )
        self._client.loop_start()
        logger.info("vehicle service started")

        try:
            while self._running:
                self._check_failsafe()
                time.sleep(0.05)
        finally:
            self.shutdown()

    def _check_failsafe(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_command_at
            if elapsed <= self._cfg.failsafe_timeout_s:
                return
            if self._timed_out:
                return
            self._timed_out = True

        logger.warning("failsafe timeout triggered after %.3fs", elapsed)
        self._motor.stop("coast")
        self._state = "stop"
        self._speed = 0
        self._publish_status("failsafe_timeout")

    def shutdown(self) -> None:
        if not self._running:
            return
        self._running = False
        logger.info("shutdown: stopping motor and MQTT")
        self._motor.stop("coast")
        self._client.loop_stop()
        try:
            self._client.disconnect()
        except Exception:
            pass
        self._motor.close()

