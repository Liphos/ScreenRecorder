"""Record the screen, mouse, keyboard and controller inputs."""

from utils.screen_recording import ScreenRecording

if __name__ == "__main__":
    # Start the screen recording
    screen_recorder = ScreenRecording(3, 10)
    screen_recorder.start()
    # Stop the screen recording
    screen_recorder.stop()
