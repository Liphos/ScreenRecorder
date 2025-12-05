import time

import mss
from PIL import ImageGrab

NB_SCREENSHOTS = 100
# Test 1: mss.mss()
start_time = time.time()
with mss.mss() as sct:
    for i in range(NB_SCREENSHOTS):
        sct.grab(sct.monitors[1])
end_time = time.time()
print(f"mss.mss() time: {end_time - start_time}")

# Test 2: ImageGrab.grab()
start_time = time.time()
for i in range(NB_SCREENSHOTS):
    ImageGrab.grab()
end_time = time.time()
print(f"ImageGrab.grab() time: {end_time - start_time}")
