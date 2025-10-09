import time
from threading import Thread

import mss


def measure_fps() -> None:
    """Measure the FPS of the screen recording."""
    sct = mss.mss()
    monitor_id = 1
    monitor = sct.monitors[monitor_id]
    mon = {
        "top": monitor["top"],
        "left": monitor["left"],
        "width": monitor["width"],
        "height": monitor["height"],
    }

    fps = 0
    last_time = time.time()

    while time.time() - last_time < 10:
        sct.grab(mon)
        fps += 1
    print(fps / 10)


if __name__ == "__main__":
    thread = Thread(target=measure_fps)
    thread.start()
    thread.join()
