import pyautogui
import time
import random

while True:
    # Move by a tiny random amount (barely visible)
    dx = random.randint(-5, 5)
    dy = random.randint(-5, 5)

    pyautogui.moveRel(dx, dy, duration=0.1)

    # Wait 30 seconds
    time.sleep(30)