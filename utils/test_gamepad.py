import threading
import time

from inputs import get_gamepad


def test_gamepad(stop_event: threading.Event):
    while not stop_event.is_set():
        events = get_gamepad()
        for event in events:
            if event.ev_type == "Key":
                if event.state == 1:
                    print(f"Button {event.code} pressed")
                elif event.state == 0:
                    print(f"Button {event.code} released")
            elif event.ev_type == "Absolute":
                print(f"Axis {event.code} value: {event.state}")


if __name__ == "__main__":
    stop_event_thread = threading.Event()
    thread = threading.Thread(target=test_gamepad, args=(stop_event_thread,))
    thread.start()
    time.sleep(10)
    stop_event_thread.set()
    thread.join()
