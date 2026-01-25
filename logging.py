import time
import os

LOG_FILE = "pico_box.log"
MAX_LOG_SIZE = 10*1024 # 10 KB

def log(msg):
    try:
        timestamp = str(int(time.time()))
        line = timestamp + " " + msg + "\n"

        # rotate log if too large
        try:
            if os.stat(LOG_FILE)[6] > MAX_LOG_SIZE:
                os.remove(LOG_FILE)
        except:
            pass

        with open(LOG_FILE, "a") as f:
            f.write(line)

    except:
        pass