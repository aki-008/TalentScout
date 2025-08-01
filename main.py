import threading
import subprocess
import sys


def run_backend():
    subprocess.run([
        sys.executable, '-m', 'uvicorn',
        'app.fastapi_main:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ])


def run_frontend():
    subprocess.run([
        sys.executable, '-m', 'streamlit',
        'run', 'app/streamlit_app.py',
        '--',
        '--server.port', '8501'
    ])


if __name__ == '__main__':
    # Launch both backend and frontend concurrently
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)
    
    backend_thread.start()
    frontend_thread.start()
    
    backend_thread.join()
    frontend_thread.join()
