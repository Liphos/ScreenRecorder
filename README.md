# ScreenRecorder
ScreenRecorder is a project that allows recording of screen, mouse, keyboard and gamepad inputs to form a dataset. The dataset will be composed of a folder containing the images (png, jpeg or webp) and a json for each input (screen timestamps, mouse, keyboard and gamepad). 
The objective is to facilitate the creation of a dataset of human-computer interactions on various tasks (exploring the web, working with Excel, playing games).
This repository adopted the one-script ideology. *main.py* contains all the code, the rest are tests and scripts to determine optimal parameters.

## Setup
The project was run with Python 3.11.9 and managed in a virtual environment with uv. To run this repository, ensure you have all the required dependencies installed by running:

```sh
pip install uv
uv sync
```

The project was tested for Linux and Windows 10/11 (even headless) but not for macOS. However, the libraries used and the code should work on macOS.

## Run
To launch the program, you only need to run main.py:
```sh
python main.py
```

By default, this will:
- Create a new dataset folder with the current date and time (e.g., `./screenshots/2025-01-13_14-30-00/`)
- Record screen at 10 FPS, keyboard, mouse, and gamepad inputs
- Stop when you press `Ctrl+Shift+Delete`

### Continue Recording to an Existing Dataset
If you specify a path to an existing dataset folder, the new recording will be **appended** to that dataset:
```sh
python main.py -o ./screenshots/2025-01-13_14-30-00/
```
The data will be separated by `NEW DATASET` markers in each log file.

## Dataset Structure
Each dataset folder contains:
| File | Description |
|------|-------------|
| `file_0.png`, `file_1.png`, ... | Screenshot images (format depends on `--format`) |
| `timestamps.txt` | Nanosecond timestamps for each screenshot |
| `keyboard_logs.json` | Keyboard press/release events with timestamps |
| `mouse_logs.json` | Mouse move, click, and scroll events with timestamps |
| `gamepad_logs.json` | Gamepad button and axis events with timestamps |
| `dataset_info.txt` | Metadata: creation timestamp and list of active recorders |

## Parameters

The script accepts the following command-line arguments:

### Input Recording Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--no-screen` | Disable screen recording | Enabled |
| `--no-keyboard` | Disable keyboard recording | Enabled |
| `--no-mouse` | Disable mouse recording | Enabled |
| `--no-gamepad` | Disable gamepad recording | Enabled |

### Output Settings
| Parameter | Description | Default |
|-----------|-------------|---------|
| `-o, --output` | Directory to save recordings. If pointing to an existing dataset, new recordings are appended. Otherwise, a timestamped subfolder is created. | `./screenshots/` |
| `--no-print-results` | Disable printing performance results | Prints results |
| `-v, --verbose` | Enable verbose output for debugging | Disabled |

### Screen Recording Settings
The screen recording offer different possible format: PNG, JPG and WEBP. PNG is a lossless compression unlike the others. In order of speed, JPG is the faster, png is 10 slower and webp 40 slower. 
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `--n-processes` | Number of parallel processes for saving screenshots. Increase for higher compression rates. | ≥1 | `2` |
| `--fps` | Target FPS for screen recording. Lower if screenshots fail to save fast enough. | ≥1 | `10` |
| `--format` | Image format for screenshots. | `png`, `jpg`, `webp` | `png` |
| `--monitor-spec` | Monitor to screenshot. Use index (1, 2, ...) or screen size as `width,height` to identify screen (e.g., `1920,1080`). | int or tuple | `1` |
| `--compression` | PNG compression level. Higher = smaller files but slower saving. | 0-9 | `6` |
| `--quality` | Quality for JPG/WEBP formats. Higher = better quality but larger files. | 0-100 | `95` |
| `--downsample` | Downsample factor for screenshots. 1 = original size, 2 = half size, etc. | ≥1 | `1` |
| `--max-screenshots` | Maximum number of screenshots before auto-stop. | ≥1 | `200000` |
| `--queue-size` | Max images allowed in queue before auto-stop (prevents out-of-memory). | ≥1 | `100` |

### Global Hotkey Settings
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--hotkey` | Hotkey to stop recording (uses [pynput format](https://pynput.readthedocs.io/en/latest/keyboard.html#global-hotkeys)) | `<ctrl>+<shift>+<delete>` |

### Timing Settings
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `--start-delay` | Delay in seconds before starting recording | ≥0 | `2.0` |
| `--timeout` | Maximum recording duration in seconds | ≥0 | `150000` |

### Examples

```sh
# Basic recording with defaults (10 FPS, PNG, all inputs)
python main.py

# High-quality JPG recording at 20 FPS with more parallel savers
python main.py --fps 20 --format jpg --quality 95 --n-processes 4

# Record only screen and keyboard, no mouse or gamepad
python main.py --no-mouse --no-gamepad

# Record a specific monitor by resolution
python main.py --monitor-spec 1920,1080

# Lightweight recording: lower FPS, more compression, downsampled
python main.py --fps 5 --compression 9 --downsample 2

# Custom output folder and custom stop hotkey
python main.py -o ./my_dataset/ --hotkey "<ctrl>+q"
```

## Additional Tools
### Fuse Datasets
In addition to the main script, there is a utility script to merge multiple datasets into one: **fuse_datasets.py**.

```sh
# Fuse two specific datasets (merges the newer into the older)
python fuse_datasets.py -f ./screenshots/2025-01-13_10-00-00/ -f2 ./screenshots/2025-01-13_11-00-00/

# Fuse all datasets in a folder into a single dataset
python fuse_datasets.py -f ./screenshots/
```

The datasets will be merged chronologically into the oldest dataset. In each file, the data will be separated by `NEW DATASET` markers.

**Warning:** This tool is not meant to handle datasets recorded in parallel. It only concatenates files in order of the first timestamp of the dataset.

### External tools
If you need to recompress the images, I recommend using XNconvert for very large dataset or Nconvert for its speed and efficiency. However it requires a license. For example to convert a dataset from png to webp and resize it, you can use the command:

```nconvert -out webp -resize 25% 25% -keepfiledate -q 85 -recurse -o ./<new_dataset>/%.webp ./<dataset>/*.png```

Or to replace the dataset:

```nconvert -out webp -resize 25% 25% -keepfiledate -q 85 -recurse -D ./<dataset>/*.png```

The script should not take a lot of ram or compute when running at a small amount of fps(10-20). However, if it is too much. I advise turning off the screen recording and using an optimized one like obs which is much more efficient. However, it records a video that needs to be converted back to images. For that I advise to use FFmpeg using a command like this one: ```ffmpeg -i input.mp4 -vf fps=1 out%d.png```. You can also specify the number of fps desired as well as the quality and format. Be aware that the conversion will take a while depending on the ressources available and the fps desired.

In term of efficiency of compression, Jpeg XL seems to be above the rest but is not always supported. Otherwise jpeg or webp are also very powerful. When checking for datasets of images for diffusion models, I found some png or jpegs. I think both can be used however less artefacts are better.

## Hardware Comparison
The project was mainly tested on two different windows machine. On both machines, I compared the performance when having cursor opened(to launch the script) as well as the light 2D game [Zombotron](https://store.steampowered.com/app/664830/Zombotron/). The script was launched with 3 saving processes and a compression ratio of 6. 

The performance for the 2 machines are:

| Machine | FPS | Processor | GPU | RAM | Screen |
|---------|-----|-----------|-----|-----|--------|
| Omen Laptop 15-dc1xxx | 13.5 | i5-9300H | GTX 1660Ti | 16GB @ 2667MHz | 1920x1080 |
| Vector 16 HX AI A2XWIG | 25 | Intel Ultra 9 275HX | RTX 5080 Laptop | 32GB @ 5600MT/s | 2560x1600 |


## Tool Comparison
I briefly tested the script using mss compared to a script in C++, thanks to a [post](https://gist.github.com/prashanthrajagopal/05f8ad157ece964d8c4d?permalink_comment_id=4790784#gistcomment-4790784). When compiling this simple script, I obtained around **30** fps on the Vector 16 laptop, which is only 5 fps more than the Python script.

A great speed improvement would be to leverage OBS or other screen recording tools as they are much more efficient (can reach **60** fps easily). However, this implies some limitations and more development time compared to Python.