"""Check if mouse detection works. left ctrl+shift+esc to stop."""

from pynput import keyboard

keys_pressed: set[keyboard.Key | keyboard.KeyCode] = set()


def on_press(key: keyboard.KeyCode | keyboard.Key | None) -> None:
    if key is None:
        return
    if isinstance(key, keyboard.KeyCode):
        print("Pressed", key.char)
    else:
        print("Pressed", key.name)
    keys_pressed.add(key)
    if keyboard.Key.shift in keys_pressed and keyboard.Key.esc in keys_pressed:
        return False


def on_release(key: keyboard.KeyCode | keyboard.Key | None) -> None:
    if key is None:
        return
    if isinstance(key, keyboard.KeyCode):
        print("Released", key.char)
    else:
        print("Released", key.name)
    if key in keys_pressed:
        keys_pressed.remove(key)


if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.join()
