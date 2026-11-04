import pytest

from deskagent.perception.accessibility import AccessibilityObserver, UIElement


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class RefreshClient:
    def __init__(self):
        self.calls = 0

    def refresh(self, identifier):
        self.calls += 1
        return UIElement(
            id=identifier, locator="ax://1/0", role="AXButton", enabled=self.calls >= 3
        )


def test_waits_until_state_matches():
    clock, client = Clock(), RefreshClient()
    observer = AccessibilityObserver(
        client, poll_interval=0.1, clock=clock, sleeper=clock.sleep
    )

    result = observer.state("button", lambda item: item.enabled, timeout=1)

    assert result.enabled is True
    assert client.calls == 3


def test_timeout_includes_description():
    clock, client = Clock(), RefreshClient()
    observer = AccessibilityObserver(
        client, poll_interval=0.1, clock=clock, sleeper=clock.sleep
    )

    with pytest.raises(TimeoutError, match="custom condition"):
        observer.state(
            "button", lambda item: False, timeout=0.2, description="custom condition"
        )


def test_cancel_interrupts_wait():
    clock, client = Clock(), RefreshClient()
    observer = AccessibilityObserver(client, clock=clock, sleeper=clock.sleep)
    observer.cancel()

    with pytest.raises(InterruptedError):
        observer.state("button", lambda item: False, timeout=1)
