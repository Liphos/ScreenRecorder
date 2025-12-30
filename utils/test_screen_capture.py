import os
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

    while time.time() - last_time < 10:
        img = sct.grab(mon)
        fps += 1
    print(fps / 10)
    # Check time to save different formats with different quality and downsample
    times = []
    # JPG
    for quality in range(5, 100, 10):
        for downsample in [1, 2, 4]:
            start = time.time()
            img_thumbnail = Image.frombytes("RGB", img.size, img.rgb)
            img_thumbnail.thumbnail(
                (img.size[0] // downsample, img.size[1] // downsample), Image.Resampling.LANCZOS
            )
            img_thumbnail.save("test_small.jpg", "JPEG", quality=quality)
            times.append(time.time() - start)
            print(
                "Quality: ",
                quality,
                "Downsample: ",
                downsample,
                "File size: ",
                round(os.path.getsize("test_small.jpg") / 1024 / 1024, 3),
                "MB",
                "Time to save: ",
                round(time.time() - start, 3),
                "s",
            )
    print("-" * 100)
    print("Mean time to save JPG: ", sum(times) / len(times))
    print("-" * 100)
    # PNG
    times = []
    for compression_rate in range(0, 10):
        for downsample in [1, 2, 4]:
            start = time.time()
            img_thumbnail = Image.frombytes("RGB", img.size, img.rgb)
            img_thumbnail.thumbnail(
                (img.size[0] // downsample, img.size[1] // downsample), Image.Resampling.LANCZOS
            )
            img_thumbnail.save("test_small.png", "PNG", compress_level=compression_rate)
            times.append(time.time() - start)
            print(
                "Compression rate: ",
                compression_rate,
                "Downsample: ",
                downsample,
                "File size: ",
                round(os.path.getsize("test_small.png") / 1024 / 1024, 3),
                "MB",
                "Time to save: ",
                round(time.time() - start, 3),
                "s",
            )
    print("-" * 100)
    print("Mean time to save PNG: ", sum(times) / len(times))
    print("-" * 100)
    # WEBP
    times = []
    for quality in range(5, 100, 10):
        for downsample in [1, 2, 4]:
            start = time.time()
            img_thumbnail = Image.frombytes("RGB", img.size, img.rgb)
            img_thumbnail.thumbnail(
                (img.size[0] // downsample, img.size[1] // downsample), Image.Resampling.LANCZOS
            )
            img_thumbnail.save("test_small.webp", "WEBP", quality=quality)
            times.append(time.time() - start)
            print(
                "Quality: ",
                quality,
                "Downsample: ",
                downsample,
                "File size: ",
                round(os.path.getsize("test_small.webp") / 1024 / 1024, 3),
                " MB",
                "Time to save: ",
                round(time.time() - start, 3),
                " s",
            )
    print("-" * 100)
    print("Mean time to save WEBP: ", sum(times) / len(times))
    print("-" * 100)


if __name__ == "__main__":
    thread = Thread(target=measure_fps)
    thread.start()
    thread.join()
