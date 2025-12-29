import time
from threading import Thread

import mss
from PIL import Image


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

    while time.time() - last_time < 2:
        img = sct.grab(mon)
        fps += 1
    Image.frombytes("RGB", img.size, img.rgb).save("test.webp", "WEBP")
    mss.tools.to_png(img.rgb, img.size, output="test.png", level=9)
    print(fps / 10)


if __name__ == "__main__":
    thread = Thread(target=measure_fps)
    thread.start()
    thread.join()
