"""Check if mouse detection works. left ctrl+shift+esc to stop."""

from pynput import keyboard

keys_pressed: set[keyboard.Key] = set()


def on_press(key):
    print("Pressed", key)
    keys_pressed.add(key)
    if (
        keyboard.Key.ctrl_l in keys_pressed
        and keyboard.Key.shift in keys_pressed
        and keyboard.Key.esc in keys_pressed
    ):
        return False


def on_release(key):
    print("Released", key)
    keys_pressed.remove(key)


if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.join()
