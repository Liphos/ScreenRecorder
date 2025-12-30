# ScreenRecorder
ScreenRecorder is a project that allows recording of screen, mouse, keyboard and gamepad inputs to form a dataset. The dataset will be composed of a folder containing the images(png, jpeg or webp) and a json for each input(screen timestamps, mouse, keyboard and gamepad). 
The objective is to facilitate the creation of a dataset of human computer interactions on several tasks(exploring the web, working with excel, playing games).
This repository adopted the one script ideology. *main.py* contains all the code, the rest are tests and scripts to determinate optimal parameters.

## Setup
The project was run with Python 3.11.9 and managed in a virtual environment with uv. To run this repository, ensure you have all the required dependencies installed by running:

```sh
pip install uv
uv sync
```

The project was tested for linux and windows 10/11(even headless) but not for Macos. However, the libraries used and the code should work on Macos.

## Run
To launch the program, you only need to run main.py
```sh
python main.py
```
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
| `-o, --output` | Directory to save recordings | `./screenshots/` |
| `--no-print-results` | Disable printing performance results | Prints results |
| `-v, --verbose` | Enable verbose output for debugging | Disabled |

### Screen Recording Settings
The screen recording offer different possible format: PNG, JPG and WEBP. PNG is a lossless compression unlike the others. In order of speed, JPG is the faster, png is 10 slower and webp 40 slower. 
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `--n-processes` | Number of parallel processes for saving screenshots. Increase for higher compression rates. | ≥1 | `2` |
| `--fps` | Target FPS for screen recording. Lower if screenshots fail to save fast enough. | ≥1 | `10` |
| `--format` | Image format for screenshots. | `png`, `jpg`, `webp` | `png` |
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

## Hardware Comparison
The project was mainly tested on two different windows machine. On both machines, I compared the performance when having cursor opened(to launch the script) as well as the light 2D game [Zombotron](https://store.steampowered.com/app/664830/Zombotron/). The script was launched with 3 saving processes and a compression ratio of 6. 

The performance for the 2 machines are:
- **13.5** fps: On an Omen Laptop 15-dc1xxx, with a i5-9300H processor, GTX 1660Ti, 16go Ram at 2667Mhz and a 1920x1080 screen size.
- **25** fps: On a Vector 16 HX AI A2XWIG, with a i ultra 9 275HX processor, RTX 5080 Laptop, 32Go Ram at 5600Mt/s and a 2560x1600 screen size.

## Tool Comparison
I briefly tested the script using mss to a script in C++, thanks to a [post](https://gist.github.com/prashanthrajagopal/05f8ad157ece964d8c4d?permalink_comment_id=4790784#gistcomment-4790784). When compiling this simple script, I obtained around **30** fps on the MSI laptop, which is only 5fps more than the python script.

A great speed improvement would be to leverage OBS or other screen recording tool as they are much more efficient(can reach **60** fps easily). However it implies some limitation and more development time compared to python.

## Additionnal tools
The script should not take a lot of ram or compute when running at a small amount of fps(10-20). However, if it is too much. I advise turning off the screen recording and using an optimized one like obs which is much more efficient. However, it records a video that needs to be converted back to images. For that I advise to use FFmpeg using a command like this one: ```ffmpeg -i input.mp4 -vf fps=1 out%d.png```. You can also specify the number of fps desired as well as the quality and format. Be aware that the conversion will take a while depending on the ressources availables and the fps desired.

In term of efficiency of compression, Jpeg XL seems to be above the rest but is not always supported. Otherwise jpeg or webp are also very powerful. When checking for dataset of images for diffusion models, I found some png or jpegs. I think both can be used however less artefacts are better.