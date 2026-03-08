import os
import time
from core.memory_manager import log_unity_error

UNITY_LOG_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Unity\Editor\Editor.log")

def unity_log_watcher():

    print(f"[LOGIS WATCHER] Monitoring Unity log: {UNITY_LOG_PATH}")

    while not os.path.exists(UNITY_LOG_PATH):
        time.sleep(5)

    with open(UNITY_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()

            if not line:
                time.sleep(0.1)
                continue

            lower_line = line.lower()

            if any(marker in lower_line for marker in ["exception","fatal","unhandled","error","assert"]):

                error_block = line

                for _ in range(5):
                    next_line = f.readline()
                    if not next_line:
                        break
                    error_block += next_line

                print(f"\033[91m[LOGIS ALERT] Unity Error Detected:\n{error_block}\033[0m")

                log_unity_error(error_block)