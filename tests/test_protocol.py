import pytest

from mini4wd.protocol import ControlMessage, build_control_payload


def test_parse_forward_payload() -> None:
    payload = b'{"action":"forward","speed":40,"stop_mode":"coast"}'
    msg = ControlMessage.from_payload(payload)
    assert msg.action == "forward"
    assert msg.speed == 40
    assert msg.stop_mode == "coast"


def test_invalid_action() -> None:
    payload = b'{"action":"left","speed":20}'
    with pytest.raises(ValueError):
        ControlMessage.from_payload(payload)


def test_build_payload_range_error() -> None:
    with pytest.raises(ValueError):
        build_control_payload(action="forward", speed=101)

