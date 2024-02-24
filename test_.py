from pynput.keyboard import Key, Listener
from pynput.mouse import Listener
import logging
# Set up logging
logging.basicConfig(filename="keyboard_activity.log", level=logging.INFO, format='%(asctime)s: %(message)s')

def on_press(key):
    print(f"{key} pressed")

def on_release(key):
    if key == Key.esc:
        # Stop listener
        return False

# Set up listener for keyboard
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()


# Set up logging for mouse activity
logging.basicConfig(filename="mouse_activity.log", level=logging.INFO, format='%(asctime)s: %(message)s')

def on_move(x, y):
    print(f"Mouse moved to ({x}, {y})")

def on_click(x, y, button, pressed):
    logging.info(f"Mouse {'pressed' if pressed else 'released'} at ({x}, {y}) with {button}")

def on_scroll(x, y, dx, dy):
    logging.info(f"Mouse scrolled at ({x}, {y}) with delta ({dx}, {dy})")

# Set up listener for mouse
with Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
    listener.join()
