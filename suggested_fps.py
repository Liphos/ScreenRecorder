"""Return suggested FPS and config for the screen recording."""

import os

from tqdm import tqdm

from main import ScreenRecording

PATH_OUTPUT = "./screenshots/temp/"


def main(
    max_processes: int = 4,
    max_fps: int = 60,
    n_screenshots: int = 500,
    verbose: bool = False,
) -> None:
    """Return suggested FPS and config for the screen recording.
    Args:
        max_processes (int): Maximum number of processes to test.
        max_fps (int): Maximum FPS to test.
        n_screenshots (int): Number of screenshots to take.
        verbose (bool): Whether to print verbose output.
    """
    best_fps = []
    most_stable_fps = []
    for n_processes in tqdm(range(1, max_processes + 1)):
        aimed_fps = max_fps
        while aimed_fps >= 10:
            if verbose:
                print(f"Testing {n_processes} processes and {aimed_fps} FPS...")
            # Create the output directory
            os.makedirs(PATH_OUTPUT, exist_ok=True)
            # Start the screen recording
            screen_recorder = ScreenRecording(
                n_processes=n_processes,
                aimed_fps=aimed_fps,
                compression_rate=6,
                max_screenshots=n_screenshots,
            )
            screen_recorder.set_common_parameters(
                path_output=PATH_OUTPUT, print_results=verbose
            )
            screen_recorder.start()
            # Stop the screen recording
            grab_log, saving_logs = screen_recorder.join()
            # Check if the config is safe
            is_unsafe = False
            # For grabbing
            grab_time = grab_log["time"]
            max_stable_fps = grab_log["max_stable_fps"]
            mean_fps = grab_log["fps"]
            if mean_fps < 0.9 * aimed_fps:
                # Config is unsafe
                is_unsafe = True
                if verbose:
                    print(
                        f"Can't record screen at {aimed_fps}, current FPS: {mean_fps}"
                    )
            # For saving
            save_times = [log["time"] for log in saving_logs]
            for save_time in save_times:
                if save_time > grab_time + 1:
                    # Config is unsafe
                    is_unsafe = True
                    if verbose:
                        print(
                            f"Save time: {save_time} is more than 1 second longer than screenshot time {grab_time}"
                        )
            if not is_unsafe:
                if verbose:
                    print(f"Most stable FPS: {max_stable_fps}")
                    print(f"Mean FPS: {mean_fps}")
                    print(f"Suggested number of processes: {n_processes}")
                    print("-" * 100)
                best_fps.append(mean_fps)
                most_stable_fps.append(max_stable_fps)
                break
            # Decrease the fps to current cap or lower
            aimed_fps = min(round(mean_fps / 10) * 10, aimed_fps - 10)
    print("-" * 100)
    print("Best config:")
    print(f"Processes: {sorted(enumerate(most_stable_fps), key=lambda x: x[1])[-1][0]}")
    print(f"Aimed FPS: {sorted(enumerate(best_fps), key=lambda x: x[1])[-1][1]}")
    print(
        f"Most stable FPS: {sorted(enumerate(most_stable_fps), key=lambda x: x[1])[-1][1]}"
    )
    print("-" * 100)


if __name__ == "__main__":
    main(verbose=True)
