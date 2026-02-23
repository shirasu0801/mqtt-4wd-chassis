from __future__ import annotations

from paho.mqtt import client as mqtt

from .config import RuntimeConfig
from .protocol import build_control_payload


class ControllerClient:
    def __init__(self, config: RuntimeConfig) -> None:
        self._cfg = config
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.mqtt.controller_client_id,
            protocol=mqtt.MQTTv311,
        )
        if config.mqtt.username:
            self._client.username_pw_set(config.mqtt.username, config.mqtt.password)

    def send(
        self,
        *,
        action: str,
        speed: int = 0,
        stop_mode: str = "coast",
        request_id: str | None = None,
    ) -> None:
        payload = build_control_payload(
            action=action,
            speed=speed,
            stop_mode=stop_mode,
            request_id=request_id,
        )
        self._client.connect(
            self._cfg.mqtt.host,
            self._cfg.mqtt.port,
            self._cfg.mqtt.keepalive,
        )
        self._client.loop_start()
        try:
            info = self._client.publish(
                self._cfg.mqtt.control_topic,
                payload=payload,
                qos=self._cfg.mqtt.qos,
                retain=False,
            )
            info.wait_for_publish(timeout=2.0)
        finally:
            self._client.loop_stop()
            self._client.disconnect()

