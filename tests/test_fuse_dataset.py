"""Unit tests for the different recording options of the main.py script."""

import json
import os
import sys
import time

sys.path.append("./")
from fuse_datasets import fuse_datasets
from main import (
    GamepadRecording,
    KeyboardRecording,
    Manager,
    MouseRecording,
    ScreenRecording,
    StopRecording,
)


def test_fuse_datasets():
    """Fuse two datasets into a single dataset."""
    current_time = time.time()
    path_output = f"./screenshots/test/FusedDataset/{current_time}/"
    for _ in range(3):
        manager = Manager(
            [
                ScreenRecording(
                    n_processes=3, aimed_fps=3, compression_rate=6, max_screenshots=1000
                ),
                KeyboardRecording(),
                MouseRecording(),
                StopRecording(),
                GamepadRecording(),
            ],
            path_output=path_output,
            print_results=False,
        )
        manager.run_until_stop(timeout=5)
    # Fuse the datasets
    fuse_datasets(path_output)
    # Check if the datasets are fused
    assert len(os.listdir(path_output)) == 1
    folder_path = os.path.join(path_output, os.listdir(path_output)[0])
    # check the dataset info
    with open(os.path.join(folder_path, "dataset_info.txt"), "r", encoding="utf-8") as f:
        recorders = f.readlines()
    str_timestamps, recorders = (
        recorders[0].split(":")[1].strip(),
        [recorder.strip() for recorder in recorders[1:]],
    )
    assert len(str_timestamps.split(",")) == 3
    # Check screen recording logs
    with open(os.path.join(folder_path, "timestamps.txt"), "r", encoding="utf-8") as f:
        timestamps = f.readlines()
    assert (
        sum(1 for line in timestamps if line.strip() == "NEW DATASET") == 2
    )  # Check the tags were added correctly
    # Check the number of images is correct
    ## Count the json and txt files
    count_json_txt_files = len(
        [
            file
            for file in os.listdir(folder_path)
            if file.endswith(".json") or file.endswith(".txt")
        ]
    )
    assert (
        len(os.listdir(folder_path))
        == len(timestamps)
        - sum(1 for line in timestamps if line.strip() == "NEW DATASET")
        + count_json_txt_files
    )
    # Check gamepad recording logs
    if os.path.exists(os.path.join(folder_path, "gamepad_logs.json")):
        with open(os.path.join(folder_path, "gamepad_logs.json"), "r", encoding="utf-8") as f:
            gamepad_logs = json.load(f)
            assert sum(1 for log in gamepad_logs if log["type"] == "NEW DATASET") == 2
    # Check keyboard recording logs
    if os.path.exists(os.path.join(folder_path, "keyboard_logs.json")):
        with open(os.path.join(folder_path, "keyboard_logs.json"), "r", encoding="utf-8") as f:
            keyboard_logs = json.load(f)
            assert sum(1 for log in keyboard_logs if log["type"] == "NEW DATASET") == 2
    # Check mouse recording logs
    if os.path.exists(os.path.join(folder_path, "mouse_logs.json")):
        with open(os.path.join(folder_path, "mouse_logs.json"), "r", encoding="utf-8") as f:
            mouse_logs = json.load(f)
            assert sum(1 for log in mouse_logs if log["type"] == "NEW DATASET") == 2
