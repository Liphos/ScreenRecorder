"""Record the screen, mouse, keyboard and controller inputs with multiprocessing."""

import os
import time
from multiprocessing import Process, Queue
from queue import Empty

import mss
import mss.tools


def _grab(queues: list[Queue], _out_queue: Queue, aimed_fps: int, number: int) -> None:
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
    out_log = {
        "log": "grabbing",
        "fps": number / (time.time() - start_time),
        "time": time.time() - start_time,
    }
    _out_queue.put(out_log)


def _save(
    queue: Queue,
    _out_queue: Queue,
    path_output: str,
    compression_rate: int,
    process_id: int,
    n_processes: int,
) -> None:
    number = 0
    output = path_output + "file_{}.png"
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
    out_log = {
        "log": "saving",
        "id": process_id,
        "fps": number / (time.time() - start_time),
        "time": time.time() - start_time,
    }
    _out_queue.put(out_log)


class ScreenRecording:
    """Screen Recording class. It captures the screen and saves the screenshots to the disk with multiprocessing."""

    def __init__(
        self,
        path_output: str = "./screenshots/",
        n_processes: int = 2,
        aimed_fps: int = 10,
        compression_rate: int = 6,
    ) -> None:
        """Initialize the screen recording.

        Args:
            n_processes (int): Number of processes to use for saving the screenshots. For high compression rate, it is recommended to use more processes. You can use measure_fps to adjust.
            aimed_fps (int): Aimed FPS for the screen recording. Lower this value when the tool fails to screenshot at the desired FPS.
            compression_rate (int, optional): Compression rate for the screenshots. Higher values means smaller files and longer saving time. Defaults to 6.
        """
        # Save parameters
        self.path_output = path_output
        self.n_processes = n_processes
        self.aimed_fps = aimed_fps
        self.compression_rate = compression_rate
        # Queues
        self._list_queues: list[Queue] = [Queue() for _ in range(n_processes)]
        self._out_queue: Queue = Queue()

        # Processes
        self._p_grab: Process | None = None
        self._p_saves: list[Process] = []

        # Create the output directory
        os.makedirs(self.path_output, exist_ok=True)

    def start(self) -> None:
        """Start the screen recording."""
        assert self.n_processes > 0, "n_processes must be 1 or more"
        # 2 processes: one for grabbing and one for saving PNG files
        # grabing is in the main process
        self._p_grab = Process(
            target=_grab, args=(self._list_queues, self._out_queue, self.aimed_fps, 100)
        )
        self._p_saves = [
            Process(
                target=_save,
                args=(
                    queue,
                    self._out_queue,
                    self.path_output,
                    self.compression_rate,
                    id,
                    self.n_processes,
                ),
            )
            for id, queue in enumerate(self._list_queues)
        ]
        self._p_grab.start()
        for p_save in self._p_saves:
            p_save.start()

    def stop(self) -> None:
        """Stop the screen recording."""
        if self._p_grab is not None:
            self._p_grab.join()
        else:
            raise ValueError("Grabbing process has not started")
        for p_save in self._p_saves:
            p_save.join()
        # Close the queues
        for queue in self._list_queues:
            queue.close()
        self._print_results()

    def _print_results(self, verbose: bool = False) -> None:
        """Print performance of the screen recording."""
        grab_fps = 0
        grab_time = None
        total_save_fps = 0
        total_save_time = 0
        log_caught = 0
        while log_caught < self.n_processes + 1:
            try:
                log = self._out_queue.get(timeout=10)
                log_caught += 1
                if log["log"] == "grabbing":
                    grab_fps = log["fps"]
                    if grab_time is None:
                        grab_time = log["time"]
                    else:
                        raise RuntimeError(
                            "Multiple grabbing logs. Only one is expected."
                        )
                elif log["log"] == "saving":
                    if verbose:
                        print(f"Saving FPS: {log['fps']} for process {log['id']}")
                    total_save_fps += log["fps"]
                    total_save_time += log["time"]
                else:
                    raise ValueError(f"Unknown log: {log}")
            except Empty as esc:
                raise Empty(
                    "Log queue not containing all logs. It is possible one process failed."
                ) from esc
        print("-" * 100)
        print(f"Grabbing FPS: {grab_fps}")
        print(f"Total saving FPS: {total_save_fps}")
        print(f"Total grab time: {grab_time}")
        print(f"Total save time: {total_save_time}")


if __name__ == "__main__":
    # Start the screen recording
    screen_recorder = ScreenRecording(
        path_output="./screenshots/", n_processes=3, aimed_fps=10
    )
    screen_recorder.start()
    # Stop the screen recording
    screen_recorder.stop()
