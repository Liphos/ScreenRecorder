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
    with open(os.path.join(folder_path_1, "dataset_info.txt"), "r", encoding="utf-8") as f:
        recorders_1 = f.readlines()
    with open(os.path.join(folder_path_2, "dataset_info.txt"), "r", encoding="utf-8") as f:
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
    different_recorders = list(set(recorders_1) ^ set(recorders_2))
    for recorder in different_recorders:
        if recorder not in NOT_IMPORTANT_RECORDER:
            raise ValueError(
                f"The recorder {recorder} is not in one of the datasets. It is important and can't be absent when fusing."
            )
    common_recorders = list(set(recorders_1) & set(recorders_2))
    for recorder in common_recorders:
        RECORDER_NAME_TO_CLASS[recorder].fuse_datasets(folder_path_1, folder_path_2)

    # Fuse the dataset info
    with open(os.path.join(folder_path_1, "dataset_info.txt"), "w", encoding="utf-8") as f:
        f.write(
            f"Timestamp: {','.join([str(timestamp) for timestamp in lst_timestamps_1 + lst_timestamps_2])}\n"
        )
        for recorder in common_recorders:
            f.write(recorder + "\n")

    # Remove the old datasets. There should be only only the dataset info file left.
    assert (
        len(os.listdir(folder_path_2)) == 1 and os.listdir(folder_path_2)[0] == "dataset_info.txt"
    )
    os.remove(os.path.join(folder_path_2, "dataset_info.txt"))
    os.rmdir(folder_path_2)
    print(
        f"The new dataset is saved in {folder_path_1}. Datasets fused successfully. The old datasets have been removed."
    )


def fuse_datasets(folder_path: str):
    """Fuse all datasets in a folder into a single dataset. The datasets are ordered by first timestamp."""
    all_datasets = []
    all_timestamps = []
    for folder in os.listdir(folder_path):
        path_sub_folder = folder_path + folder + "/"
        if os.path.exists(os.path.join(path_sub_folder, "dataset_info.txt")):
            all_datasets.append(path_sub_folder)
            with open(
                os.path.join(path_sub_folder, "dataset_info.txt"), "r", encoding="utf-8"
            ) as f:
                str_timestamps = f.readlines()[0].split(":")[1].strip()
                lst_timestamps = [float(timestamp) for timestamp in str_timestamps.split(",")][0]
                all_timestamps.append(lst_timestamps)
        else:
            print(f"The folder {path_sub_folder} is not a valid dataset. Skipping.")
    index_sort = sorted(enumerate(all_timestamps), key=lambda x: x[1])
    for index, timestamp in index_sort[1:]:
        fuse_two_datasets(all_datasets[index_sort[0][0]], all_datasets[index])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--folder_path",
        type=str,
        required=True,
        help="Path to the folder containing the datasets.",
    )
    parser.add_argument(
        "-f2",
        "--folder_path2",
        type=str,
        default=None,
        help="Path to the folder containing the second dataset. If not provided, the datasets inside the folder_path will be fused timewise.",
    )
    args = parser.parse_args()
    if args.folder_path2 is None:
        fuse_datasets(args.folder_path)
    else:
        fuse_two_datasets(args.folder_path, args.folder_path2)
