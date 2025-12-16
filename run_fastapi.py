#!/usr/bin/env python
# Launch FastAPI WebRTC server
# Usage: python webrtc_server_fastapi.py
# Or: python webrtc_server_fastapi.py --port 8090 --host 0.0.0.0

import subprocess
import sys

if __name__ == "__main__":
    # Run with uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "webrtc_server_fastapi:app",
        "--host", "0.0.0.0",
        "--port", "8090",
        "--reload"
    ])
