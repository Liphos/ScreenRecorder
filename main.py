"""Record the screen, mouse, keyboard and controller inputs with multiprocessing."""

import argparse
import ctypes
import json
import os
import threading
import time
import warnings
from abc import ABC, abstractmethod
from multiprocessing import Process, Queue, Value
from queue import Empty
from typing import Any, Dict, List, Tuple

import mss
import mss.tools
from inputs import UnpluggedError, devices, get_gamepad
from PIL import Image
from pynput import keyboard, mouse


def colorful_warning(message, category, filename, lineno, line=None) -> str:
    # ANSI escape codes for colors
    yellow = "\033[93m"
    red = "\033[91m"
    reset = "\033[0m"
    if isinstance(category, RuntimeWarning):
        return f"{red}ERROR: {message}{reset}\n"
    else:
        return f"{yellow}WARNING: {message}{reset}\n"


# Override the default warning format
warnings.formatwarning = colorful_warning


def _grab(
    queues: list[Queue],
    _out_queue: Queue,
    stop_flag: ctypes.c_bool,
    aimed_fps: int,
    max_screenshots: int = 100_000,
    verbose: bool = False,
) -> None:
    """Process that take screenshots at desired FPS and send them to the queues.

    Args:
        queues (list[Queue]): Queues to send the screenshots to give to the saving processes.
        _out_queue (Queue): Queue to send the logs to at the end.
        stop_flag (ctypes.c_bool): Flag to stop the process from the main process.
        aimed_fps (int): Desired FPS for the screenshots.
        max_screenshots (int, optional): Maximum number of screenshots before stopping. Defaults to 100_000.
        verbose (bool, optional): Control how much information is printed. Useful for debugging. Defaults to False.
    """
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
    for i in range(max_screenshots):
        if stop_flag.value:
            break
        queue = queues[i % len(queues)]
        queue.put(sct.grab(rect))
        all_timestamps.append(time.time())
        time.sleep(max(0, 1 / aimed_fps - (time.perf_counter() - grab_time)))
        max_stable_fps = min(max_stable_fps, int(1 / (time.perf_counter() - grab_time)))
        grab_time = time.perf_counter()
    if verbose:
        print("Stop screenshotting. Give empty image to saving workers to stop.")
    # Tell the other worker to stop
    for queue in queues:
        queue.put(None)
    out_log = {
        "log": "grabbing",
        "fps": len(all_timestamps) / (time.time() - start_time),
        "time": time.time() - start_time,
        "max_stable_fps": max_stable_fps,
        "timestamps": all_timestamps,
    }
    _out_queue.put(out_log)
    if verbose:
        print("Grabbing worker finished and output logs.")


def _save(
    queue: Queue,
    _out_queue: Queue,
    path_output: str,
    compression_rate: int,
    process_id: int,
    n_processes: int,
    format_image: str,
    verbose: bool = False,
) -> None:
    """Process that saves the screenshots to the disk.
    Args:
        queue (Queue): Queue to get the screenshots from.
        _out_queue (Queue): Queue to send the logs to at the end.
        path_output (str): Path to save the screenshots to.
        compression_rate (int): Compression rate for the screenshots.
        process_id (int): ID of the process.
        n_processes (int): Number of processes.
        format_image (str): Format to save the screenshots to. Use Pillow's available formats(eg: "png", "jpg", "webp").
        verbose (bool, optional): Control how much information is printed. Useful for debugging. Defaults to False.
    """

    def save_to_disk(img: mss.screenshot.ScreenShot, number: int) -> None:
        """Save the screenshot to the disk."""
        output = path_output + f"file_{number * n_processes + process_id}." + format_image
        if format_image == "png":
            mss.tools.to_png(img.rgb, img.size, level=compression_rate, output=output)
        elif format_image == "jpg":
            Image.frombytes("RGB", img.size, img.rgb).save(
                output,
                "JPEG",
            )
        elif format_image == "webp":
            Image.frombytes("RGB", img.size, img.rgb).save(
                output,
                "WEBP",
            )
        else:
            raise ValueError(f"Invalid format: {format_image}")

    number = 0
    start_time = time.time()
    while "there are screenshots":
        try:
            img: mss.screenshot.ScreenShot | None = queue.get(timeout=60)
        except Empty:
            warnings.warn(
                f"WARNING: Saving worker {process_id} queue is empty. Did the grabbing process stop?",
                RuntimeWarning,
            )
            break
        if img is None:
            break
        save_to_disk(img, number)
        number += 1
    if verbose:
        print(f"Saving worker {process_id} finished and creating logs.")
    out_log = {
        "log": "saving",
        "id": process_id,
        "fps": number / (time.time() - start_time),
        "time": time.time() - start_time,
    }
    _out_queue.put(out_log)
    if verbose:
        print(f"Saving worker {process_id} sending logs to main process.")


class Recorder(ABC):
    """Abstract class for all recorders."""

    def __init__(self) -> None:
        self.verbose: bool
        self.path_output: str
        self.print_results: bool
        self.is_stopped: bool = False

    def set_common_parameters(
        self, path_output: str, print_results: bool, verbose: bool = False
    ) -> None:
        """Set parameters common to all recorders."""
        self.path_output = path_output
        self.print_results = print_results
        self.verbose = verbose

    def check_availability(self) -> Exception | None:
        """Check if the recorder is available."""
        return None

    def start(self) -> None:
        self._start()

    def should_stop(self) -> bool:
        should_stop = self._should_stop()
        if self.verbose and should_stop:
            print(f"{self.__class__.__name__} called for stop.")
        return should_stop

    def stop(self) -> None:
        self._stop()
        self.is_stopped = True
        if self.verbose:
            print(f"{self.__class__.__name__} recording stop flag set.")

    def join(self) -> Any:
        assert self.is_stopped, "Recorder is not stopped. Call stop() first."
        logs = self._join()
        if self.verbose:
            print(f"{self.__class__.__name__} recording finished.")
        return logs

    @abstractmethod
    def _start(self) -> None:
        """Used to start the recording."""

    @abstractmethod
    def _should_stop(self) -> bool:
        """Used to return flag to stop the recording."""

    @abstractmethod
    def _stop(self) -> None:
        """Used to return flag to stop the recording."""

    @abstractmethod
    def _join(self) -> Any:
        """Used to wait for the recording to finish."""


class ScreenRecording(Recorder):
    """Screen Recording class. It captures the screen and saves the screenshots to the disk with multiprocessing."""

    def __init__(
        self,
        n_processes: int = 2,
        aimed_fps: int = 10,
        format_image: str = "png",
        compression_rate: int = 6,
        max_screenshots: int = 100_000,
        allowed_n_images_delayed: int = 100,
    ) -> None:
        """Initialize the screen recording.

        Args:
            n_processes (int): Number of processes to use for saving the screenshots. For high compression rate, it is recommended to use more processes. You can use measure_fps to adjust.
            aimed_fps (int): Aimed FPS for the screen recording. Lower this value when the tool fails to screenshot at the desired FPS.
            format_image (str, optional): Format to save the screenshots to. Use Pillow's available formats(eg: "png", "jpg", "webp"). Defaults to "png".
            compression_rate (int, optional): Compression rate for the screenshots. Higher values means smaller files and longer saving time. Only applies to PNG format. Defaults to 6.
            max_screenshots (int, optional): Option to stop recording after a certain number of screenshots is taken. Defaults to 100_000.
            allowed_n_images_delayed (int, optional): Allowed number of images accumulated in the queue. If it exceeds, the process will call stop to protect current colleted data. Defaults to 100.
        """

        super().__init__()
        self.n_processes = n_processes
        self.aimed_fps = aimed_fps
        self.format_image = format_image
        self.compression_rate = compression_rate
        self.max_screenshots = max_screenshots
        self.allowed_n_images_delayed = allowed_n_images_delayed
        # Queues
        self._list_queues: list[Queue] = [
            Queue(self.allowed_n_images_delayed) for _ in range(n_processes)
        ]
        self._out_queue: Queue = Queue()
        self._stop_flag = Value(ctypes.c_bool, False)

        # Processes
        self._p_grab: Process | None = None
        self._p_saves: list[Process] = []

    def check_availability(self) -> Exception | None:
        with mss.mss() as sct:
            try:
                _ = {
                    "top": sct.monitors[1]["top"],
                    "left": sct.monitors[1]["left"],
                    "width": sct.monitors[1]["width"],
                    "height": sct.monitors[1]["height"],
                }
            except Exception as e:
                raise UnpluggedError("No screen found.") from e
        return None

    def _start(self) -> None:
        """Start the screen recording."""
        assert self.n_processes > 0, "n_processes must be 1 or more"
        # 2 processes: one for grabbing and one for saving PNG files
        # grabing is in the main process
        self._p_grab = Process(
            target=_grab,
            args=(
                self._list_queues,
                self._out_queue,
                self._stop_flag,
                self.aimed_fps,
                self.max_screenshots,
                self.verbose,
            ),
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
                    self.format_image,
                    self.verbose,
                ),
            )
            for id, queue in enumerate(self._list_queues)
        ]
        self._p_grab.start()
        for p_save in self._p_saves:
            p_save.start()

    def _should_stop(self) -> bool:
        """Call to stop if grabbing process has stopped or if the number of images accumulated in the saving queues exceeds the allowed number."""
        assert self._p_grab is not None, "Grabbing process has not started. Call start() first."
        if any(queue.full() for queue in self._list_queues):
            warnings.warn(
                f"WARNING: Out of memory: Stopping recording because the number of images accumulated in the saving queues exceeds the allowed number: allowed_n_images_delayed={self.allowed_n_images_delayed}. Consider increasing the number of processes or decreasing the aimed FPS.",
                RuntimeWarning,
            )
            return True
        return not self._p_grab.is_alive()

    def _stop(self) -> None:
        """Stop the screen recording."""
        self._stop_flag.value = True

    def _join(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Stop the screen recording."""
        logs: List[Dict[str, Any]] = []
        while len(logs) < self.n_processes + 1:
            # Wait for all logs to be received
            try:
                log = self._out_queue.get(timeout=60)
                logs.append(log)
            except Empty:
                warnings.warn(
                    f"WARNING: Log queue waiting out after receiving {len(logs)}/{self.n_processes + 1} logs. "
                    + "One saving process might be still running or have failed.",
                    RuntimeWarning,
                )
        print(f"All {len(logs)} logs received.")
        # After all logs are received, the processes should have been finished
        if self._p_grab is not None:
            self._p_grab.join()
        else:
            raise ValueError("Grabbing process has not started")
        for p_save in self._p_saves:
            p_save.join()
        # Close the queues
        for queue in self._list_queues:
            queue.close()
        self._out_queue.close()
        grab_log, saving_logs = self._get_logs(logs)
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

    def _get_logs(self, logs: List[Dict[str, Any]]) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        saving_logs: List[Dict[str, Any]] = []
        grab_log: Dict[str, Any] = {}
        for log in logs:
            if log["log"] == "grabbing":
                assert not grab_log, (
                    "Multiple grabbing logs means multiple screen recording processes. Only one is expected."
                )
                grab_log = log
            elif log["log"] == "saving":
                saving_logs.append(log)
            else:
                raise ValueError(f"Unknown log: {log}")
        return (grab_log, saving_logs)

    def _print_results(self, grab_log: Dict[str, Any], saving_logs: List[Dict[str, Any]]) -> None:
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


class KeyboardRecording(Recorder):
    """Keyboard Recording class. It captures the keyboard inputs and saves the data to a separate file."""

    def on_press(self, key: keyboard.KeyCode | keyboard.Key | None) -> None:
        """Called when pressing a key."""
        if key is None:
            return
        self._action_logs.append(
            {
                "timestamp": time.time(),
                "type": "pressed",
                "key": key.char if isinstance(key, keyboard.KeyCode) else key.name,
            }
        )

    def on_release(self, key: keyboard.KeyCode | keyboard.Key | None) -> None:
        """Called when releasing a key."""
        if key is None:
            return
        self._action_logs.append(
            {
                "timestamp": time.time(),
                "type": "release",
                "key": key.char if isinstance(key, keyboard.KeyCode) else key.name,
            }
        )

    def __init__(self) -> None:
        super().__init__()
        self._action_logs: List[Dict[str, Any]] = []
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )

    def _start(self) -> None:
        """Start the keyboard recording."""
        self.keyboard_listener.start()

    def _stop(self) -> None:
        """Stop the keyboard recording."""
        self.keyboard_listener.stop()

    def _should_stop(self) -> bool:
        """Call to stop if keyboard recording has stopped."""
        return not self.keyboard_listener.is_alive()

    def _join(self) -> None:
        """Wait for the keyboard recording to finish and save the logs."""
        self.keyboard_listener.join(timeout=10)
        if self.keyboard_listener.is_alive():
            warnings.warn("WARNING: Keyboard listener did not stop.")
        with open(self.path_output + "keyboard_logs.json", "w", encoding="utf-8") as f:
            json.dump(self._action_logs, f)


class MouseRecording(Recorder):
    """Mouse Recording class. It captures the mouse inputs and saves the data to a separate file."""

    def on_move(self, x: int, y: int):
        """Called when moving the mouse."""
        self._action_logs.append({"timestamp": time.time(), "type": "move", "x": x, "y": y})

    def on_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        """Called when clicking the mouse."""
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
        """Called when scrolling the mouse."""
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
        super().__init__()
        self._action_logs: List[Dict[str, Any]] = []
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll
        )

    def _start(self) -> None:
        """Start the mouse recording."""
        self.mouse_listener.start()

    def _stop(self) -> None:
        """Stop the mouse recording."""
        self.mouse_listener.stop()

    def _should_stop(self) -> bool:
        """Call to stop if mouse recording has stopped."""
        return not self.mouse_listener.is_alive()

    def _join(self) -> None:
        """Wait for the mouse recording to finish and save the logs."""
        self.mouse_listener.join(timeout=10)
        if self.mouse_listener.is_alive():
            warnings.warn("WARNING: Mouse listener did not stop.")
        with open(self.path_output + "mouse_logs.json", "w", encoding="utf-8") as f:
            json.dump(self._action_logs, f)


class StopRecording(Recorder):
    """Stop the recording if hotkey is pressed.
    Args:
        hotkey (str, optional): Hotkey to stop the recording. It follows the format of pynput. Defaults to "<ctrl>+<shift>+<esc>".
    """

    def __init__(self, hotkey: str = "<ctrl>+<shift>+<delete>") -> None:
        super().__init__()
        self.hotkey_listener = keyboard.GlobalHotKeys(
            {
                hotkey: self._return_flag,
            }
        )
        self.hotkey_pressed = False

    def _should_stop(self) -> bool:
        return self.hotkey_pressed

    def _start(self) -> None:
        self.hotkey_listener.start()

    def _return_flag(self) -> None:
        """Return flag to stop the recording"""
        self.hotkey_pressed = True

    def _stop(self) -> None:
        self.hotkey_listener.stop()

    def _join(self) -> None:
        self.hotkey_listener.join(timeout=10)
        if self.hotkey_listener.is_alive():
            warnings.warn("WARNING: Hotkey listener did not stop.")


class GamepadRecording(Recorder):
    """Gamepad Recording class. It captures the gamepad inputs and saves the data to a separate file."""

    def get_gamepad_inputs(self) -> None:
        """Thread that captures the gamepad inputs"""
        while not self._stop_event.is_set():
            events = get_gamepad()
            for event in events:
                if event.ev_type == "Key":
                    if event.state == 1:
                        self._action_logs.append(
                            {
                                "timestamp": time.time(),
                                "type": "pressed",
                                "key": event.code,
                            }
                        )
                    elif event.state == 0:
                        self._action_logs.append(
                            {
                                "timestamp": time.time(),
                                "type": "released",
                                "key": event.code,
                            }
                        )
                elif event.ev_type == "Absolute":
                    self._action_logs.append(
                        {
                            "timestamp": time.time(),
                            "type": "absolute",
                            "axis": event.code,
                            "value": event.state,
                        }
                    )

    def __init__(self) -> None:
        super().__init__()
        self._action_logs: List[Dict[str, str | int | float | bool]] = []
        self._stop_event = threading.Event()
        self._gamepad_thread = threading.Thread(
            target=self.get_gamepad_inputs,
        )
        self._gamepad_thread.daemon = True

    def check_availability(self) -> Exception | None:
        try:
            _ = devices.gamepads[0]
            return None
        except IndexError:
            # No gamepad found
            return UnpluggedError("No gamepad found.")

    def _start(self) -> None:
        self._gamepad_thread.start()

    def _stop(self) -> None:
        self._stop_event.set()

    def _join(self) -> None:
        # Add a timeout here as an exception because the gampad thread won't stop until a gamepad input is detected
        # TODO: Find a way to add a timeout
        self._gamepad_thread.join(timeout=10)
        if self._gamepad_thread.is_alive():
            warnings.warn("WARNING: Gamepad thread did not stop.")
        # Dump the action logs to a file
        time_to_save = time.time()
        with open(self.path_output + "gamepad_logs.json", "w", encoding="utf-8") as f:
            json.dump(self._action_logs, f)
        print(f"Time to save gamepad logs: {time.time() - time_to_save:.2f} seconds")

    def _should_stop(self) -> bool:
        return not self._gamepad_thread.is_alive()


class Manager:
    """Manager class. It manages the different recorders and saves the data to the disk."""

    def __init__(
        self,
        list_recorders: list[Recorder],
        path_output: str = "./screenshots/",
        print_results: bool = True,
        verbose: bool = False,
    ) -> None:
        """Initialize the manager and recorders.

        Args:
            list_recorders (list[Recorder]): List of recorders to manage.
            path_output (str, optional): Directory to save screenshots and data. Defaults to "./screenshots/".
            print_results (bool, optional): Print the performance of the screen recording. Defaults to True.
            verbose (bool, optional): Control how much information is printed. Useful for debugging. Defaults to False.
        """

        # Save parameters
        self.path_output = (
            path_output + time.strftime("%Y-%m-%d_%H-%M-%S") + "/"
        )  # Create a subdirectory with the current date and time
        self.print_results = print_results
        self.list_recorders = list_recorders
        self.verbose = verbose
        # Create the output directory
        os.makedirs(self.path_output, exist_ok=True)
        # Set parameters common to all recorders
        for recorder in list_recorders:
            recorder.set_common_parameters(self.path_output, self.print_results, self.verbose)
        self.is_stopped = False  # Flag to check if stop() has been called

    def start(self) -> None:
        # Check availability of all recorders and remove recorders that are not available
        remaining_recorders: List[Recorder] = []
        for recorder in self.list_recorders:
            exception = recorder.check_availability()
            if exception is None:
                remaining_recorders.append(recorder)
            else:
                warnings.warn(
                    f"WARNING: Recorder {recorder.__class__.__name__} is not available: {exception}"
                    + "This recorder will not be used."
                )
        self.list_recorders = remaining_recorders
        # Start the recorders that are available
        for recorder in self.list_recorders:
            recorder.start()

    def stop(self) -> None:
        for recorder in self.list_recorders:
            recorder.stop()
        self.is_stopped = True
        print("Stopping recording.")

    def join(self) -> Any:
        print("Waiting for recording to stop.")
        assert self.is_stopped, "Manager is not stopped. Call stop() first."
        for recorder in self.list_recorders:
            recorder.join()
        print("Recording finished.")

    def run_until_stop(self, start_delay: float = 0, timeout: float = 150_000) -> None:
        """Run the manager until the stop() method is called.
        Args:
            start_delay (float, optional): Delay in seconds before starting the recording. Defaults to 0.
            timeout (float, optional): Timeout in seconds. Defaults to 150_000.
        """
        time.sleep(start_delay)
        start_time = time.time()
        self.start()
        print("Recording started.")
        while time.time() - start_time < timeout:
            time.sleep(0.1)
            for recorder in self.list_recorders:
                if recorder.should_stop():
                    self.stop()
                    self.join()
                    return
        print("Timeout reached.")
        self.stop()
        self.join()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Record screen, mouse, keyboard and controller inputs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # What inputs to record
    recording_group = parser.add_argument_group("Input Recording Options")
    recording_group.add_argument(
        "--no-screen", action="store_true", help="Disable screen recording"
    )
    recording_group.add_argument(
        "--no-keyboard", action="store_true", help="Disable keyboard recording"
    )
    recording_group.add_argument("--no-mouse", action="store_true", help="Disable mouse recording")
    recording_group.add_argument(
        "--no-gamepad", action="store_true", help="Disable gamepad recording"
    )

    # Where to save the recordings
    output_group = parser.add_argument_group("Output Settings")
    output_group.add_argument(
        "-o",
        "--output",
        type=str,
        default="./screenshots/",
        help="Directory to save recordings",
    )
    output_group.add_argument(
        "--no-print-results",
        action="store_true",
        help="Disable printing performance results",
    )
    output_group.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output for debugging"
    )

    # Screen recording settings
    screen_group = parser.add_argument_group(
        "Screen Recording Settings. Only used if screen recording is enabled."
    )
    screen_group.add_argument(
        "--n-processes",
        type=int,
        default=2,
        help="Number of processes for saving screenshots",
    )
    screen_group.add_argument(
        "--fps",
        type=int,
        default=10,
        help="Target FPS for screen recording(Recommended: 10-20). Lower this value when the tool fails to screenshot at the desired FPS.",
    )
    screen_group.add_argument(
        "--format",
        type=str,
        default="png",
        choices=["png", "jpg", "webp"],
        help='Format to save the screenshots to. Use Pillow\'s available formats(eg: "png", "jpg", "webp").',
    )
    screen_group.add_argument(
        "--compression",
        type=int,
        default=9,
        choices=range(0, 10),
        metavar="[0-9]",
        help="PNG compression rate (0=none, 9=max). Higher values means smaller files but longer saving time.",
    )
    screen_group.add_argument(
        "--max-screenshots",
        type=int,
        default=200_000,
        help="Stop condition: Maximum number of screenshots before stopping",
    )
    screen_group.add_argument(
        "--queue-size",
        type=int,
        default=100,
        help="Allowed number of images in queue before auto-stop. Used to avoid out of memory errors.",
    )

    # Hotkey settings
    hotkey_group = parser.add_argument_group("Global Hotkey Settings")
    hotkey_group.add_argument(
        "--hotkey",
        type=str,
        default="<ctrl>+<shift>+<delete>",
        help="Stop condition: Hotkey to stop recording (pynput format)",
    )

    # Timing settings
    timing_group = parser.add_argument_group("Timing Settings")
    timing_group.add_argument(
        "--start-delay",
        type=float,
        default=2.0,
        help="Delay in seconds before starting recording",
    )
    timing_group.add_argument(
        "--timeout",
        type=float,
        default=150_000,
        help="Stop condition: Timeout in seconds for recording from start",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Build list of recorders based on arguments
    recorders: List[Recorder] = []

    # Always add stop recording for hotkey support
    recorders.append(StopRecording(hotkey=args.hotkey))

    # Add recorders based on flags
    if not args.no_screen:
        recorders.append(
            ScreenRecording(
                n_processes=args.n_processes,
                aimed_fps=args.fps,
                format_image=args.format,
                compression_rate=args.compression,
                max_screenshots=args.max_screenshots,
                allowed_n_images_delayed=args.queue_size,
            )
        )
    if not args.no_keyboard:
        recorders.append(KeyboardRecording())
    if not args.no_mouse:
        recorders.append(MouseRecording())
    if not args.no_gamepad:
        recorders.append(GamepadRecording())
    if len(recorders) == 0:
        raise ValueError(
            "Argument error: No recording type specified. Add at least one recording type."
        )

    # Create and run manager
    manager = Manager(
        recorders,
        path_output=args.output,
        print_results=not args.no_print_results,
        verbose=args.verbose,
    )
    manager.run_until_stop(start_delay=args.start_delay, timeout=args.timeout)


if __name__ == "__main__":
    main()
