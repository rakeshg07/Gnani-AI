"""Convenience script to run the VoiceIQ India FastAPI backend."""
import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure UTF-8 output on Windows consoles
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    # Ensure current directory is in sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    print("=" * 60)
    print(">> Starting VoiceIQ India FastAPI Backend Server")
    print(">> API Base: http://127.0.0.1:8000")
    print(">> Swagger Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
