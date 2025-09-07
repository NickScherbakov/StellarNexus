#!/usr/bin/env python3
"""
StellarNexus Web Server Launcher
Starts the FastAPI web application with auto-reload
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the FastAPI web server"""
    # Add the api directory to Python path
    api_dir = Path(__file__).parent / "api"
    sys.path.insert(0, str(api_dir))

    # Change to the project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print("🚀 Starting StellarNexus Web Server...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")

    # Launch uvicorn with auto-reload
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info"
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()