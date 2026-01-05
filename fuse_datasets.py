"""Fuse datasets in a folder into a single dataset."""

import argparse
import os
from typing import Dict, Type

from main import (
    GamepadRecording,
    KeyboardRecording,
    MouseRecording,
    Recorder,
    ScreenRecording,
    StopRecording,
)

NOT_IMPORTANT_RECORDER = ["StopRecording"]


RECORDER_NAME_TO_CLASS: Dict[str, Type[Recorder]] = {
    "GamepadRecording": GamepadRecording,
    "KeyboardRecording": KeyboardRecording,
    "MouseRecording": MouseRecording,
    "ScreenRecording": ScreenRecording,
    "StopRecording": StopRecording,
}


def fuse_two_datasets(folder_path_1: str, folder_path_2: str) -> None:
    """Fuse two datasets into a single dataset."""
    # Check if the datasets are compatible
    ## Reorder with old dataset first
    with open(folder_path_1 + "dataset_info.txt", "r", encoding="utf-8") as f:
        recorders_1 = f.readlines()
    with open(folder_path_2 + "dataset_info.txt", "r", encoding="utf-8") as f:
        recorders_2 = f.readlines()
    str_timestamps_1, recorders_1 = (
        recorders_1[0].split(":")[1].strip(),
        [recorder.strip() for recorder in recorders_1[1:]],
    )
    str_timestamps_2, recorders_2 = (
        recorders_2[0].split(":")[1].strip(),
        [recorder.strip() for recorder in recorders_2[1:]],
    )
    # Convert the timestamps to a list of floats
    lst_timestamps_1 = [float(timestamp) for timestamp in str_timestamps_1.split(",")]
    lst_timestamps_2 = [float(timestamp) for timestamp in str_timestamps_2.split(",")]
    assert (
        lst_timestamps_1[0] > lst_timestamps_2[-1] or lst_timestamps_2[0] > lst_timestamps_1[-1]
    ), "The datasets are ordered timewise. Can't handle datasets done at the same time for now."
    if lst_timestamps_1[0] > lst_timestamps_2[-1]:
        recorders_1, recorders_2 = recorders_2, recorders_1
        folder_path_1, folder_path_2 = folder_path_2, folder_path_1
        lst_timestamps_1, lst_timestamps_2 = lst_timestamps_2, lst_timestamps_1
    ## Check the recorders are the same except for the not important recorders
    different_recorders = list(set(recorders_1) - set(recorders_2))
    for recorder in different_recorders:
        if recorder not in NOT_IMPORTANT_RECORDER:
            raise ValueError(
                f"The recorder {recorder} is not in one of the datasets. It is important and can't be absent when fusing."
            )
    common_recorders = list(set(recorders_1) & set(recorders_2))
    for recorder in common_recorders:
        RECORDER_NAME_TO_CLASS[recorder].fuse_datasets(folder_path_1, folder_path_2)

    # Fuse the dataset info
    with open(folder_path_1 + "dataset_info.txt", "w", encoding="utf-8") as f:
        f.write(
            f"Timestamp: {','.join([str(timestamp) for timestamp in lst_timestamps_1 + lst_timestamps_2])}\n"
        )
        for recorder in common_recorders:
            f.write(recorder + "\n")

    # Remove the old datasets. There should be only only the dataset info file left.
    assert (
        len(os.listdir(folder_path_2)) == 1 and os.listdir(folder_path_2)[0] == "dataset_info.txt"
    )
    os.remove(folder_path_2 + "dataset_info.txt")
    os.rmdir(folder_path_2)
    print(
        f"The new dataset is saved in {folder_path_1}. Datasets fused successfully. The old datasets have been removed."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder_path_1", type=str, required=True)
    parser.add_argument("--folder_path_2", type=str, required=True)
    args = parser.parse_args()
    fuse_two_datasets(args.folder_path_1, args.folder_path_2)
