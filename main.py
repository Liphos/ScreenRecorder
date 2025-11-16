"""Record the screen, mouse, keyboard and controller inputs with multiprocessing."""

import json
import os
import time
from abc import ABC, abstractmethod
from multiprocessing import Process, Queue
from queue import Empty
from typing import Any, Dict, List, Optional

import mss
import mss.tools
from pynput import keyboard, mouse


def _grab(queues: list[Queue], _out_queue: Queue, aimed_fps: int, number: int) -> None:
    sct = mss.mss()
    all_timestamps = []
    monitor_id = 1
    rect = {
        "top": sct.monitors[monitor_id]["top"],
        "left": sct.monitors[monitor_id]["left"],
        "width": sct.monitors[monitor_id]["width"],
        "height": sct.monitors[monitor_id]["height"],
    }
    start_time = time.time()
    grab_time = time.perf_counter()
    max_stable_fps = 10_000
    for i in range(number):
        queue = queues[i % len(queues)]
        queue.put(sct.grab(rect))
        all_timestamps.append(time.time())
        time.sleep(max(0, 1 / aimed_fps - (time.perf_counter() - grab_time)))
        max_stable_fps = min(max_stable_fps, int(1 / (time.perf_counter() - grab_time)))
        grab_time = time.perf_counter()

    # Tell the other worker to stop
    for queue in queues:
        queue.put(None)
    out_log = {
        "log": "grabbing",
        "fps": number / (time.time() - start_time),
        "time": time.time() - start_time,
        "max_stable_fps": max_stable_fps,
        "timestamps": all_timestamps,
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


class Recorder(ABC):
    """Abstract class for all recorders."""

    def __init__(self) -> None:
        self.path_output: str
        self.print_results: bool

    def set_common_parameters(self, path_output: str, print_results: bool) -> None:
        """Set parameters common to all recorders."""
        self.path_output = path_output
        self.print_results = print_results

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> Any:
        pass


class ScreenRecording(Recorder):
    """Screen Recording class. It captures the screen and saves the screenshots to the disk with multiprocessing."""

    def __init__(
        self,
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

        super().__init__()
        self.n_processes = n_processes
        self.aimed_fps = aimed_fps
        self.compression_rate = compression_rate
        # Queues
        self._list_queues: list[Queue] = [Queue() for _ in range(n_processes)]
        self._out_queue: Queue = Queue()

        # Processes
        self._p_grab: Process | None = None
        self._p_saves: list[Process] = []

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

    def stop(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
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
        grab_log, saving_logs = self._get_logs()
        self._save_timestamps(grab_log)
        if self.print_results:
            self._print_results(grab_log, saving_logs)
        return grab_log, saving_logs

    def _save_timestamps(self, grab_log: Dict[str, Any]) -> None:
        """Save the timestamps of the screen recording to a file."""
        with open(self.path_output + "timestamps.txt", "w", encoding="utf-8") as f:
            for incr, timestamp in enumerate(grab_log["timestamps"]):
                if incr == len(grab_log["timestamps"]) - 1:
                    f.write(f"{timestamp:.6f}")
                else:
                    f.write(f"{timestamp:.6f}\n")

    def _get_logs(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        log_caught = 0
        saving_logs: List[Dict[str, Any]] = []
        grab_log: Dict[str, Any] = {}
        while log_caught < self.n_processes + 1:
            try:
                log = self._out_queue.get(timeout=10)
                log_caught += 1
                if log["log"] == "grabbing":
                    grab_log = log
                    assert (
                        grab_log != {}
                    ), "Multiple grabbing logs means multiple screen recording processes. Only one is expected."
                elif log["log"] == "saving":
                    saving_logs.append(log)
                else:
                    raise ValueError(f"Unknown log: {log}")
            except Empty as esc:
                raise Empty(
                    "Log queue not containing all logs. It is possible one process failed."
                ) from esc
        return (grab_log, saving_logs)

    def _print_results(
        self, grab_log: Dict[str, Any], saving_logs: List[Dict[str, Any]]
    ) -> None:
        """Print performance of the screen recording. Return the logs."""
        grab_fps = round(grab_log["fps"], 2)
        grab_time = round(grab_log["time"], 2)
        lst_save_fps = [round(log["fps"] * self.n_processes, 2) for log in saving_logs]
        lst_save_time = [round(log["time"], 2) for log in saving_logs]
        print("-" * 100)
        print(f"Process grab FPS: {grab_fps}")
        print(f"Processes saving FPS: {lst_save_fps}")
        print(f"Process grab time: {grab_time}")
        print(f"Processes save time: {lst_save_time}")


class InputRecording(Recorder):
    def on_press(self, key: keyboard.KeyCode | keyboard.Key):
        self._action_logs.append(
            {
                "timestamp": time.time(),
                "type": "pressed",
                "key": key.char if isinstance(key, keyboard.KeyCode) else key.name,
            }
        )

    def on_release(self, key: keyboard.KeyCode | keyboard.Key):
        self._action_logs.append(
            {
                "timestamp": time.time(),
                "type": "release",
                "key": key.char if isinstance(key, keyboard.KeyCode) else key.name,
            }
        )

    def on_move(self, x: int, y: int):
        self._action_logs.append(
            {"timestamp": time.time(), "type": "move", "x": x, "y": y}
        )

    def on_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        self._action_logs.append(
            {
                "timestamp": time.time(),
                "type": "click",
                "x": x,
                "y": y,
                "button": button.name,
                "is_pressed": pressed,
            }
        )

    def on_scroll(self, x: int, y: int, dx: int, dy: int):
        self._action_logs.append(
            {
                "timestamp": time.time(),
                "type": "scroll",
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
            }
        )

    def __init__(self) -> None:
        # Define variables and create word file
        super().__init__()
        self._action_logs: List[Dict[str, Any]] = []
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll
        )

    def start(self) -> None:
        # Start the keyboard recording
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop(self) -> None:
        # Stop the keyboard recording
        # Dump the action logs to a file
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        # Join the listeners
        self.keyboard_listener.join()
        self.mouse_listener.join()
        with open(self.path_output + "action_logs.json", "w", encoding="utf-8") as f:
            json.dump(self._action_logs, f)


class Manager:
    """Manager class. It manages the different recorders and saves the data to the disk."""

    def __init__(
        self,
        list_recorders: list[Recorder],
        path_output: str = "./screenshots/",
        print_results: bool = True,
    ) -> None:
        """Initialize the manager and recorders.

        Args:
            list_recorders (list[Recorder]): List of recorders to manage.
            path_output (str, optional): Directory to save screenshots and data. Defaults to "./screenshots/".
            print_results (bool, optional): Print the performance of the screen recording. Defaults to True.
        """

        # Save parameters
        self.path_output = (
            path_output + time.strftime("%Y-%m-%d_%H-%M-%S") + "/"
        )  # Create a subdirectory with the current date and time
        self.print_results = print_results
        self.list_recorders = list_recorders
        # Create the output directory
        os.makedirs(self.path_output, exist_ok=True)
        # Set parameters common to all recorders
        for recorder in list_recorders:
            recorder.set_common_parameters(self.path_output, self.print_results)

    def start(self) -> None:
        for recorder in self.list_recorders:
            recorder.start()

    def stop(self) -> Any:
        for recorder in self.list_recorders:
            recorder.stop()


if __name__ == "__main__":
    # Start the screen recording
    manager = Manager(
        [
            ScreenRecording(n_processes=3, aimed_fps=10, compression_rate=6),
            InputRecording(),
        ]
    )
    manager.start()
    # Stop the screen recording
    manager.stop()
