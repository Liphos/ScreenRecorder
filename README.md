# ScreenRecorder
ScreenRecorder is a project that allows recording of screen, mouse, keyboard and gamepad inputs to form a dataset. 
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
## Hardware Comparison
The project was mainly tested on two different windows machine. On both machines, I compared the performance when having cursor opened(to launch the script) as well as tbe light 2D game [Zombotron](https://store.steampowered.com/app/664830/Zombotron/). The script was launched with 3 saving processes and a compression ratio of 6. 

The performance for the 2 machines are:
- **13.5** fps: On an Omen Laptop 15-dc1xxx, with a i5-9300H processor, GTX 1660Ti, 16go Ram at 2667Mhz and a 1920x1080 screen size.
- **25** fps: On a Vector 16 HX AI A2XWIG, with a i ultra 9 275HX processor, RTX 5080 Laptop, 32Go Ram at 5600Mt/s and a 2560x1600 screen size.

## Tool Comparison
I briefly tested the script using mss to a script in C++, thanks to a [post](https://gist.github.com/prashanthrajagopal/05f8ad157ece964d8c4d?permalink_comment_id=4790784#gistcomment-4790784). When compiling this simple script, I obtained around **30** fps on the MSI laptop, which is only 5fps more than the python script.

A great speed improvement would be to leverage OBS or other screen recording tool as they are much more efficient(can reach **60** fps easily). However it implies some limitation and more development time compared to python.


## Additionnal tools
To convert png images to webp: ```ffmpeg -i <file_name.png> -q:v 90 "<new_image_name>.webp"``` where -q:v 90 is the quality ratio(higher is better)

In term of efficiency of compression, Jpeg XL seems to be above the rest but is not always supported. Otherwise jpeg or webp are also very powerful. When checking for dataset of images for diffusion models, I found some png or jpegs. I think both can be used however less artefacts are better.