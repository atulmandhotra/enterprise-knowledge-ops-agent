from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import threading


PORT = 8080

CHROMA_DIR = Path("/app/chroma_db")
MARKER = CHROMA_DIR / ".ingestion_complete"

_app_process = None


def set_app_process(process):
    global _app_process
    _app_process = process


def is_app_alive():
    """
    During document ingestion, the main container process is alive
    even though Streamlit has not started yet.

    Once Streamlit starts, check whether the Streamlit process is alive.
    """
    if _app_process is None:
        return True

    return _app_process.poll() is None


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        # ----------------------------------------
        # Liveness
        # ----------------------------------------

        if self.path == "/health/live":

            if is_app_alive():
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(503)
                self.end_headers()

            return

        # ----------------------------------------
        # Readiness
        # ----------------------------------------

        if self.path == "/health/ready":

            if MARKER.exists() and is_app_alive():

                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"READY")

            else:

                self.send_response(503)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"NOT READY")

            return

        # ----------------------------------------
        # Unknown endpoint
        # ----------------------------------------

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Disable HTTP access logs for health checks.
        return


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    thread.start()

    print(f"Health server started on port {PORT}")