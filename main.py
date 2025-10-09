import time
from multiprocessing import Process, Queue

import mss
import mss.tools


def grab(list_queues: list[Queue], number: int, aimed_fps: int) -> None:
    sct = mss.mss()
    monitor_id = 1
    rect = {
        "top": sct.monitors[monitor_id]["top"],
        "left": sct.monitors[monitor_id]["left"],
        "width": sct.monitors[monitor_id]["width"],
        "height": sct.monitors[monitor_id]["height"],
    }
    start_time = time.time()
    grab_time = time.perf_counter()
    for i in range(number):
        queue = list_queues[i % len(list_queues)]
        queue.put(sct.grab(rect))
        time.sleep(max(0, 1 / aimed_fps - (time.perf_counter() - grab_time)))
        grab_time = time.perf_counter()

    # Tell the other worker to stop
    for queue in list_queues:
        queue.put(None)
    print(f"Grabbing took {time.time() - start_time} seconds")
    print("Grabbing FPS:", number / (time.time() - start_time))


def save(queue: Queue, compression: int, id: int, n_workers: int) -> None:
    number = 0
    output = "screenshots/file_{}.png"
    to_png = mss.tools.to_png
    start_time = time.time()
    while "there are screenshots":
        img = queue.get()
        if img is None:
            break

        to_png(
            img.rgb,
            img.size,
            output=output.format(number * n_workers + id),
            level=compression,
        )
        number += 1
    print(f"Saving took {time.time() - start_time} seconds")
    print("Saving FPS:", number * n_workers / (time.time() - start_time))


if __name__ == "__main__":
    # The screenshots queue
    n_lists = 3
    list_queues: list[Queue] = [Queue() for _ in range(n_lists)]

    # 2 processes: one for grabbing and one for saving PNG files
    # grabing is in the main process
    p_grab = Process(target=grab, args=(list_queues, 600, 10))
    p_saves = [
        Process(target=save, args=(queue, 6, id, n_lists))
        for id, queue in enumerate(list_queues)
    ]
    p_grab.start()
    for p_save in p_saves:
        p_save.start()
    # Wait for the processes to finish
    p_grab.join()
    for p_save in p_saves:
        p_save.join()
    # Close the queues
    for queue in list_queues:
        queue.close()
