from __future__ import annotations

from abc import ABC, abstractmethod


class BaseMotorDriver(ABC):
    @abstractmethod
    def forward(self, speed: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def reverse(self, speed: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self, stop_mode: str = "coast") -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class MockMotorDriver(BaseMotorDriver):
    def __init__(self) -> None:
        self.state = "stop"
        self.speed = 0

    def forward(self, speed: int) -> None:
        self.state = "forward"
        self.speed = speed
        print(f"[motor] forward speed={speed}")

    def reverse(self, speed: int) -> None:
        self.state = "reverse"
        self.speed = speed
        print(f"[motor] reverse speed={speed}")

    def stop(self, stop_mode: str = "coast") -> None:
        self.state = "stop"
        self.speed = 0
        print(f"[motor] stop mode={stop_mode}")

    def close(self) -> None:
        self.stop("coast")


class DRV8833MotorDriver(BaseMotorDriver):
    def __init__(self, ain1_pin: int, ain2_pin: int, pwm_frequency_hz: int = 1000) -> None:
        try:
            from gpiozero import PWMOutputDevice
        except Exception as exc:
            raise RuntimeError(
                "gpiozero unavailable. Install optional dependency: pip install '.[pi]'"
            ) from exc

        self._in1 = PWMOutputDevice(ain1_pin, frequency=pwm_frequency_hz, initial_value=0.0)
        self._in2 = PWMOutputDevice(ain2_pin, frequency=pwm_frequency_hz, initial_value=0.0)

    @staticmethod
    def _duty(speed: int) -> float:
        clamped = max(0, min(100, speed))
        return clamped / 100.0

    def forward(self, speed: int) -> None:
        duty = self._duty(speed)
        self._in2.value = 0.0
        self._in1.value = duty

    def reverse(self, speed: int) -> None:
        duty = self._duty(speed)
        self._in1.value = 0.0
        self._in2.value = duty

    def stop(self, stop_mode: str = "coast") -> None:
        if stop_mode == "brake":
            self._in1.value = 1.0
            self._in2.value = 1.0
            return
        self._in1.value = 0.0
        self._in2.value = 0.0

    def close(self) -> None:
        self.stop("coast")
        self._in1.close()
        self._in2.close()

