"""Unit tests for the different recording options of the main.py script."""

import sys


sys.path.append("../recorder")
from main import (
    GamepadRecording,
    KeyboardRecording,
    Manager,
    MouseRecording,
    ScreenRecording,
    StopRecording,
)


def test_screen_recording():
    manager = Manager(
        [
            ScreenRecording(
                n_processes=3, aimed_fps=10, compression_rate=6, max_screenshots=100
            ),
        ],
        path_output="./screenshots/test/",
        print_results=False,
    )
    manager.run_until_stop(timeout=100)


def test_input_recording():
    manager = Manager(
        [
            KeyboardRecording(),
            MouseRecording(),
            StopRecording(),
        ],
        path_output="./screenshots/test/",
        print_results=False,
    )
    manager.run_until_stop(timeout=10)


def test_gamepad_recording():
    manager = Manager(
        [
            GamepadRecording(),
        ],
        path_output="./screenshots/test/",
        print_results=False,
    )
    manager.run_until_stop(timeout=10)


def test_external_stop():
    manager = Manager(
        [
            ScreenRecording(
                n_processes=3, aimed_fps=10, compression_rate=6, max_screenshots=1000
            ),
        ],
        path_output="./screenshots/test/",
        print_results=False,
    )
    manager.run_until_stop(timeout=10)


def test_combined_recording():
    manager = Manager(
        [
            ScreenRecording(
                n_processes=3, aimed_fps=10, compression_rate=6, max_screenshots=1000
            ),
            KeyboardRecording(),
            MouseRecording(),
            StopRecording(),
            GamepadRecording(),
        ],
        path_output="./screenshots/test/",
        print_results=False,
    )
    manager.run_until_stop(timeout=10)
