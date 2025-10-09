"""Screen Recording utility. It captures the screen and saves the screenshots to the disk with multiprocessing."""

import time
from multiprocessing import Process, Queue

import mss
import mss.tools


class ScreenRecording:
    """Screen Recording class. It captures the screen and saves the screenshots to the disk with multiprocessing."""

    def __init__(
        self, n_processes: int, aimed_fps: int, compression_rate: int = 6
    ) -> None:
        """Initialize the screen recording.

        Args:
            n_processes (int): Number of processes to use for saving the screenshots. For high compression rate, it is recommended to use more processes. You can use measure_fps to adjust.
            aimed_fps (int): Aimed FPS for the screen recording. Lower this value when the tool fails to screenshot at the desired FPS.
            compression_rate (int, optional): Compression rate for the screenshots. Higher values means smaller files and longer saving time.. Defaults to 6.
        """
        self.n_processes = n_processes
        self.aimed_fps = aimed_fps
        self.compression_rate = compression_rate
        self.list_queues: list[Queue] = [Queue() for _ in range(n_processes)]

        # Processes
        self.p_grab: Process | None = None
        self.p_saves: list[Process] = []

    def start(self) -> None:
        """Start the screen recording."""
        # 2 processes: one for grabbing and one for saving PNG files
        # grabing is in the main process
        self.p_grab = Process(
            target=_grab, args=(self.list_queues, self.aimed_fps, 600)
        )
        self.p_saves = [
            Process(
                target=_save,
                args=(queue, self.compression_rate, id, self.n_processes),
            )
            for id, queue in enumerate(self.list_queues)
        ]
        self.p_grab.start()
        for p_save in self.p_saves:
            p_save.start()

    def stop(self) -> None:
        """Stop the screen recording."""
        if self.p_grab is not None:
            self.p_grab.join()
        else:
            raise ValueError("Grabbing process has not started")
        for p_save in self.p_saves:
            p_save.join()
        # Close the queues
        for queue in self.list_queues:
            queue.close()


def _grab(queues: list[Queue], aimed_fps: int, number: int) -> None:
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
        queue = queues[i % len(queues)]
        queue.put(sct.grab(rect))
        time.sleep(max(0, 1 / aimed_fps - (time.perf_counter() - grab_time)))
        grab_time = time.perf_counter()

    # Tell the other worker to stop
    for queue in queues:
        queue.put(None)
    print(f"Grabbing took {time.time() - start_time} seconds")
    print("Grabbing FPS:", number / (time.time() - start_time))


def _save(
    queue: Queue, compression_rate: int, process_id: int, n_processes: int
) -> None:
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
            output=output.format(number * n_processes + process_id),
            level=compression_rate,
        )
        number += 1
    print(f"Saving took {time.time() - start_time} seconds")
    print("Saving FPS:", number * n_processes / (time.time() - start_time))
