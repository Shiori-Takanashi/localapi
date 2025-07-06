# tools/launch_servers.py
import subprocess
from pathlib import Path
import sys
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = BASE_DIR / "server"
PYTHON_CMD = "python" if sys.platform.startswith("win") else "python3"

commands = [
    [PYTHON_CMD, str(SERVER_DIR / "fast_server.py")],
    [PYTHON_CMD, str(SERVER_DIR / "flask_server.py")],
    [PYTHON_CMD, str(SERVER_DIR / "flask_gunicorn_server.py")],
]

procs = []

try:
    for cmd in commands:
        print(f"起動: {' '.join(cmd)}")
        # Windowsの場合は別コンソールで起動も可能（任意）
        flags = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
        procs.append(subprocess.Popen(cmd, creationflags=flags))

    for proc in procs:
        proc.wait()

except KeyboardInterrupt:
    print("停止要求検出。全サーバ終了中...")
    for proc in procs:
        proc.terminate()
