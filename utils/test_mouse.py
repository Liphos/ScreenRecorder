"""Check if mouse detection works."""

from pynput import mouse


def on_move(x, y):
    print(f"Pointer moved to {x},{y}")


def on_click(x, y, button, pressed):
    print(button)
    print("Pressed" if pressed else "Released", x, y)
    if not pressed:
        # Stop listener
        return False


def on_scroll(x, y, dx, dy):
    print(f"Scrolled {'down' if dy < 0 else 'up'} at {x},{y}")


if __name__ == "__main__":
    # Collect events until released
    with mouse.Listener(
        on_move=on_move, on_click=on_click, on_scroll=on_scroll
    ) as listener:
        listener.join()

    # ...or, in a non-blocking fashion:
    listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    listener.start()
